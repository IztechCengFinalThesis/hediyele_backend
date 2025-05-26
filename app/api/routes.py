from fastapi import APIRouter, HTTPException, Body, Depends, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError, BaseModel
from app.schemas.schemas import ProductFilterSchema, LoginCredentials
from app.services.crud import query_products
from app.db.database import get_db_connection
from app.services.firebase import FirebaseAuth, PremiumAuth, AdminAuth, is_premium_user, set_user_premium_status
import openai
import os
import json
import re
from app.services import blind_test
from app.services.firebase import signin_with_email_password
from typing import Optional, List

router = APIRouter()
router.include_router(blind_test.router, prefix="/blind-test")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Firebase auth dependencies
firebase_auth = FirebaseAuth()  # Basic auth için
premium_auth = PremiumAuth()    # Premium auth için
admin_auth = AdminAuth()        # Admin auth için
# Admin işlemleri için schema
class PremiumStatusUpdate(BaseModel):
    user_id: str
    is_premium: bool = True

@router.post("/admin/set-premium")
async def set_premium(
    data: PremiumStatusUpdate,
    admin = Depends(admin_auth)  # Sadece premium kullanıcılar bu işlemi yapabilsin
):
    """
    Admin endpoint to set a user's premium status using Firebase custom claims.
    Only accessible to premium users (as a simple admin check).
    """
    try:
        result = set_user_premium_status(data.user_id, data.is_premium)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/token", response_model=dict)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    This endpoint is used by the Swagger UI for authentication.
    """
    try:
        # Sign in with Firebase
        auth_result = signin_with_email_password(
            form_data.username,  # username field is used for email in OAuth2 form
            form_data.password
        )
        
        # Extract token
        token = auth_result.get("idToken")
        
        return {
            "access_token": token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/login")
async def login(credentials: LoginCredentials):
    """
    Login endpoint using email and password for Firebase authentication.
    Returns a token that can be used with the Authorization header.
    """
    try:
        # Sign in with Firebase
        auth_result = signin_with_email_password(
            credentials.email, credentials.password
        )
        
        # Extract token and user data
        id_token = auth_result.get("idToken")
        user_id = auth_result.get("localId")
        user_email = auth_result.get("email")
        
        return {
            "status": "success",
            "message": "Giriş başarılı!",
            "token": id_token,
            "user_id": user_id,
            "user_email": user_email
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.get("/user/status")
async def check_user_status(user = Depends(firebase_auth)):
    """
    Return user status information including whether they have premium access.
    """
    is_premium = is_premium_user(user)
    
    return {
        "status": "success",
        "user_id": user.get("uid"),
        "user_email": user.get("email"),
        "is_premium": is_premium,
        "subscription_type": "premium" if is_premium else "basic"
    }

@router.get("/db-check/")
async def check_db_connection():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM PRODUCT;")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return {
            "status": "success",
            "message": "✅ Veritabanı bağlantısı başarılı!",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Veritabanı bağlantısı başarısız! Hata: {str(e)}"
        }


@router.get("/auth-check/")
async def check_auth(user = Depends(firebase_auth)):
    """
    This endpoint checks if the Firebase authentication is working.
    It requires a valid Firebase token in the Authorization header.
    """
    return {
        "status": "success",
        "message": "Authentication successful",
        "user_id": user.get("uid"),
        "user_email": user.get("email")
        }


@router.post("/recommendations/basic/")
async def get_basic_recommendations(
    raw_filters: ProductFilterSchema = Body(...),
    user = Depends(firebase_auth)
):
    try:
        product_recommendations = query_products(raw_filters.model_dump())
        return {
            "message": "Öneriler hazır!",
            "filters_used": raw_filters.model_dump(),
            "recommendations": product_recommendations
        }

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendations/premium")
async def get_premium_recommendations(
    user_input: str, 
    previous_filled_data: dict = None,
    user = Depends(premium_auth)  # FirebaseAuth yerine PremiumAuth kullan
):
    try:
        filter_dict = previous_filled_data or ProductFilterSchema().model_dump()

        prompt = f"""
        Kullanıcıdan şu giriş alındı: {user_input}
        Mevcut doldurulmuş tablo:
        {json.dumps(filter_dict, indent=4)}

        Bu tabloyu kullanıcı bilgisine göre **güncelle** ve sadece eksik bilgileri tamamla.
        Daha önce doldurulmuş bilgileri değiştirme.
        Boolean değişkenleri True veya False olarak döndür. Null kullanma.
        
        NOT: Kullanıcı bütçe konusunda konuştuğunda MUTLAKA şu şekilde davran:
        1. Eğer kullanıcı net bir aralık belirttiyse (örn. "200-300 TL arası" gibi) min_budget ve max_budget'i o şekilde ayarla.
        2. Eğer kullanıcı tek bir değer belirttiyse (örn. "500 TL civarı" gibi) bir aralık oluştur:
           - min_budget = belirtilen değerin %20 altı
           - max_budget = belirtilen değerin %20 üstü
        3. Eğer kullanıcı "ucuz olsun" gibi belirsiz ifadeler kullandıysa, min_budget=0, max_budget=300 gibi belirleme yapabilirsin.
        4. Eğer kullanıcı "pahalı olsun" veya "lüks" gibi ifadeler kullandıysa, min_budget=1000 gibi bir alt sınır belirleyebilirsin.
        5. Kullanıcı bütçe konusunda hiçbir şey söylemediyse, min_budget ve max_budget'i null bırak.
        
        JSON formatında sadece güncellenmiş tabloyu döndür.
        """

        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Sen bir asistan olarak kullanıcı girdisine göre tabloyu tamamlıyorsun. Daha önce doldurulmuş bilgileri değiştirme. JSON formatında sadece tabloyu döndür. Boolean değişkenleri True veya False olarak döndür."},
                {"role": "user", "content": prompt}
            ]
        )

        raw_content = response.choices[0].message.content.strip()
        cleaned_content = re.sub(r"```json\n(.*?)\n```", r"\1", raw_content, flags=re.DOTALL).strip()

        updated_data = json.loads(cleaned_content)

        # Eksik alanlar önceki verilerle doldurulsun
        for key, value in filter_dict.items():
            if key not in updated_data or updated_data[key] is None:
                updated_data[key] = value

        # Bütçe işleme mantığını kontrol et ve gerekirse düzelt
        if "min_budget" in updated_data and "max_budget" in updated_data:
            min_budget = updated_data.get("min_budget")
            max_budget = updated_data.get("max_budget")
            
            # Hem min hem max aynı değere sahipse ve null değilse
            if min_budget is not None and max_budget is not None and min_budget == max_budget:
                # Aynı değeri merkez alarak aralık oluştur
                budget_value = min_budget
                updated_data["min_budget"] = round(budget_value * 0.8)  # %20 altı
                updated_data["max_budget"] = round(budget_value * 1.2)  # %20 üstü

        filled_filters = ProductFilterSchema(**updated_data)
        missing_fields = filled_filters.get_missing_fields()

        # Bütçe kontrolü
        has_budget = False
        if filled_filters.min_budget is not None or filled_filters.max_budget is not None:
            has_budget = True

        if missing_fields:
            field_messages = {
                "Yaş aralığını belirtir misiniz?": ("age", "Aslında hediyeyi düşündüğünüz kişinin yaş aralığını bilmem çok yardımcı olacak. Genç biri mi yoksa yetişkin biri için mi bakıyorsunuz?"),
                "Hediye alacağınız kişinin cinsiyeti nedir?": ("gender", "Bu hediyeyi bir erkek için mi yoksa bir kadın için mi düşünüyorsunuz? Bu bilgi önerilerimi daha isabetli yapacak."),
                "Bu hediye özel bir gün için mi? (Doğum günü, yıl dönümü vb.)": ("special", "Merak ediyorum, bu hediye özel bir kutlama için mi? Doğum günü, yıldönümü veya başka özel bir gün olabilir mi?"),
                "Kişinin ilgi alanlarından birkaçını paylaşır mısınız? (Örneğin, spor, müzik, teknoloji vb.)": ("interests", "Hediye düşündüğünüz kişi nelerden hoşlanır? Belki spor, müzik, kitap okumak ya da başka hobiler... Biraz bahsedebilir misiniz?")
            }

            first_missing = missing_fields[0]
            field_key, _ = field_messages.get(first_missing, ("unknown", "Bana biraz daha bilgi verebilir misiniz?"))

            # Check if the input is in English using AI
            language_detection_prompt = f"Determine if the following text is in English. Respond with only 'true' or 'false': '{user_input}'"
            
            language_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a language detection assistant. Respond with only 'true' for English text and 'false' for non-English text."},
                    {"role": "user", "content": language_detection_prompt}
                ]
            )
            
            is_english = language_response.choices[0].message.content.strip().lower() == 'true'

            # Create appropriate prompt based on language
            if is_english:
                message_prompt = f"Convert this message to a natural, conversational English response: '{first_missing}'"
            else:
                message_prompt = f"Şu mesajı doğal, sohbet tarzında ama kısa bir şekilde söyle: '{first_missing}'"

            message_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a gift assistant. Respond naturally and conversationally in the same language as the user's input."},
                    {"role": "user", "content": message_prompt}
                ]
            )
            
            natural_message = message_response.choices[0].message.content.strip()

            return {
                "message": natural_message,
                "field_key": field_key,
                "filled_table": updated_data
            }

        # Eğer bütçe belirtilmemişse ve diğer tüm alanlar dolmuşsa bütçe soralım
        if not has_budget:
            # Check if the input is in English using AI
            language_detection_prompt = f"Determine if the following text is in English. Respond with only 'true' or 'false': '{user_input}'"
            
            language_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a language detection assistant. Respond with only 'true' for English text and 'false' for non-English text."},
                    {"role": "user", "content": language_detection_prompt}
                ]
            )
            
            is_english = language_response.choices[0].message.content.strip().lower() == 'true'

            if is_english:
                budget_prompt = "Do you have a budget in mind for the gift? It would help me make better recommendations."
            else:
                budget_prompt = "Hediye için düşündüğünüz bir bütçe var mı? Uygun önerilerim için bilmem yardımcı olur."
            
            return {
                "message": budget_prompt,
                "field_key": "budget",
                "filled_table": updated_data
            }
        
        # Ürün önerileri için SQL sorgusu oluştur ve çalıştır
        product_recommendations = query_products(filled_filters.model_dump())

        if not product_recommendations["products"]:
            # Check if the input is in English using AI
            language_detection_prompt = f"Determine if the following text is in English. Respond with only 'true' or 'false': '{user_input}'"
            
            language_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a language detection assistant. Respond with only 'true' for English text and 'false' for non-English text."},
                    {"role": "user", "content": language_detection_prompt}
                ]
            )
            
            is_english = language_response.choices[0].message.content.strip().lower() == 'true'

            if is_english:
                no_products_prompt = "Hmm, I couldn't find any products that exactly match your criteria. Would you like me to try a broader search?"
            else:
                no_products_prompt = "Hmm, aradığınız kriterlere tam uyan bir ürün bulamadım. Biraz daha geniş bir arama yapmamı ister misiniz?"
            
            return {
                "message": no_products_prompt,
                "filled_table": updated_data
            }

        # Check if the input is in English using AI
        language_detection_prompt = f"Determine if the following text is in English. Respond with only 'true' or 'false': '{user_input}'"
        
        language_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a language detection assistant. Respond with only 'true' for English text and 'false' for non-English text."},
                {"role": "user", "content": language_detection_prompt}
            ]
        )
        
        is_english = language_response.choices[0].message.content.strip().lower() == 'true'

        if is_english:
            success_message = "Great! I've prepared some gift recommendations just for you. I hope you like them!"
        else:
            success_message = "Harika! Size özel hediye önerilerim hazır. Umarım beğenirsiniz!"
        
        return {
            "message": success_message,
            "filled_table": updated_data,
            "recommendations": product_recommendations
        }

    except json.JSONDecodeError:
        return {
            "error": "Üzgünüm, yanıtınızı anlayamadım. Lütfen tekrar dener misiniz?",
            "raw_response": raw_content
        }
    except Exception as e:
        return {"error": f"Bir sorun oluştu: {str(e)}. Tekrar deneyebilir miyiz?"}

@router.get("/products/{product_id}/images")
async def get_product_images(
    product_id: int, 
    image_id: Optional[int] = None,
    user = Depends(firebase_auth)  # Normal auth ekledim
):
    """
    Ürün ID'sine göre resimleri getirir.
    Eğer image_id belirtilirse sadece o resmi döndürür, aksi halde tüm resimlerin listesini döndürür.
    Bu endpoint için normal kullanıcı kimlik doğrulaması gereklidir.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if image_id is not None:
            # Belirli bir resmi getir
            cur.execute(
                "SELECT image_data FROM product_images WHERE product_id = %s AND id = %s ORDER BY image_order",
                (product_id, image_id)
            )
            result = cur.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail="Belirtilen resim bulunamadı")
            
            image_data = result[0]
            cur.close()
            conn.close()
            
            # Binary resim verisini doğrudan döndür
            return Response(content=bytes(image_data), media_type="image/png")
        else:
            # Ürüne ait tüm resimlerin listesini getir
            cur.execute(
                "SELECT id, image_order FROM product_images WHERE product_id = %s ORDER BY image_order",
                (product_id,)
            )
            results = cur.fetchall()
            
            if not results:
                raise HTTPException(status_code=404, detail="Bu ürüne ait resim bulunamadı")
            
            image_list = [{"image_id": row[0], "order": row[1], "url": f"/api/products/{product_id}/images?image_id={row[0]}"} for row in results]
            cur.close()
            conn.close()
            
            return {"product_id": product_id, "images": image_list}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resim getirme hatası: {str(e)}")


@router.get("/public/products/{product_id}/images")
async def get_public_product_images(product_id: int, image_id: Optional[int] = None):
    """
    Ürün ID'sine göre resimleri getirir. Bu endpoint kimlik doğrulaması gerektirmez.
    Eğer image_id belirtilirse sadece o resmi döndürür, aksi halde tüm resimlerin listesini döndürür.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if image_id is not None:
            # Belirli bir resmi getir
            cur.execute(
                "SELECT image_data FROM product_images WHERE product_id = %s AND id = %s ORDER BY image_order",
                (product_id, image_id)
            )
            result = cur.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail="Belirtilen resim bulunamadı")
            
            image_data = result[0]
            cur.close()
            conn.close()
            
            # Binary resim verisini doğrudan döndür
            return Response(content=bytes(image_data), media_type="image/png")
        else:
            # Ürüne ait tüm resimlerin listesini getir
            cur.execute(
                "SELECT id, image_order FROM product_images WHERE product_id = %s ORDER BY image_order",
                (product_id,)
            )
            results = cur.fetchall()
            
            if not results:
                raise HTTPException(status_code=404, detail="Bu ürüne ait resim bulunamadı")
            
            image_list = [{"image_id": row[0], "order": row[1], "url": f"/api/public/products/{product_id}/images?image_id={row[0]}"} for row in results]
            cur.close()
            conn.close()
            
            return {"product_id": product_id, "images": image_list}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resim getirme hatası: {str(e)}")


@router.get("/products/{product_id}/thumbnail")
async def get_product_thumbnail(
    product_id: int,
    user = Depends(firebase_auth)  # Normal auth ekledim
):
    """
    Ürün ID'sine göre ilk resmi (thumbnail) döndürür.
    Bu endpoint için normal kullanıcı kimlik doğrulaması gereklidir.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # İlk sıradaki resmi getir (image_order'a göre sıralı)
        cur.execute(
            "SELECT image_data FROM product_images WHERE product_id = %s ORDER BY image_order LIMIT 1",
            (product_id,)
        )
        result = cur.fetchone()
        
        if not result:
            # Eğer resim bulunamazsa default bir resim döndürülebilir
            # Ya da 404 hatası verilebilir
            raise HTTPException(status_code=404, detail="Bu ürüne ait resim bulunamadı")
        
        image_data = result[0]
        cur.close()
        conn.close()
        
        # Binary resim verisini doğrudan döndür
        return Response(content=bytes(image_data), media_type="image/png")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Thumbnail getirme hatası: {str(e)}")


@router.get("/public/products/{product_id}/thumbnail")
async def get_public_product_thumbnail(product_id: int):
    """
    Ürün ID'sine göre ilk resmi (thumbnail) döndürür. Bu endpoint kimlik doğrulaması gerektirmez.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # İlk sıradaki resmi getir (image_order'a göre sıralı)
        cur.execute(
            "SELECT image_data FROM product_images WHERE product_id = %s ORDER BY image_order LIMIT 1",
            (product_id,)
        )
        result = cur.fetchone()
        
        if not result:
            # Eğer resim bulunamazsa default bir resim döndürülebilir
            # Ya da 404 hatası verilebilir
            raise HTTPException(status_code=404, detail="Bu ürüne ait resim bulunamadı")
        
        image_data = result[0]
        cur.close()
        conn.close()
        
        # Binary resim verisini doğrudan döndür
        return Response(content=bytes(image_data), media_type="image/png")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Thumbnail getirme hatası: {str(e)}")
