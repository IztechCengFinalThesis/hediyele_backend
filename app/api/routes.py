from fastapi import APIRouter, HTTPException, Body, Depends, status
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

        Ayrıca `min_budget` ve `max_budget` alanlarını da kullanıcı girişinden tahmin etmeye çalış.
        Bu alanlar float sayı olmalı (örn. 250.0 veya 999.99 gibi).
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

        filled_filters = ProductFilterSchema(**updated_data)
        missing_fields = filled_filters.get_missing_fields()

        if missing_fields:
            field_messages = {
                "Yaş aralığını belirtir misiniz?": ("age", "Lütfen yaş aralığını belirtin."),
                "Hediye alacağınız kişinin cinsiyeti nedir?": ("gender", "Lütfen cinsiyeti belirtin."),
                "Bu hediye özel bir gün için mi? (Doğum günü, yıl dönümü vb.)": ("special", "Bu hediye özel bir gün için mi?"),
                "Kişinin ilgi alanlarından birkaçını paylaşır mısınız? (Örneğin, spor, müzik, teknoloji vb.)": ("interests", "Kişinin ilgi alanlarını paylaşır mısınız?")
            }

            first_missing = missing_fields[0]
            field_key, next_prompt = field_messages.get(first_missing, ("unknown", "Eksik bilgi girin."))

            return {
                "message": first_missing,
                "field_key": field_key,
                "filled_table": updated_data,
                "next_prompt": next_prompt
            }

        product_recommendations = query_products(filled_filters.model_dump())

        if not product_recommendations["products"]:
            return {
                "message": "Bu kriterlere uygun ürün bulunamadı, daha genel bir filtreleme yapmayı deneyelim mi?",
                "filled_table": updated_data,
                "next_prompt": "Lütfen filtreleri biraz daha esneterek tekrar deneyin."
            }

        return {
            "message": "Ürün önerileri oluşturuldu!",
            "filled_table": updated_data,
            "recommendations": product_recommendations
        }

    except json.JSONDecodeError:
        return {
            "error": "Yanıt JSON formatında değil.",
            "raw_response": raw_content
        }
    except Exception as e:
        return {"error": f"Hata oluştu: {str(e)}"}
