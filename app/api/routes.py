from fastapi import APIRouter, HTTPException, Body
from pydantic import ValidationError
from app.schemas.schemas import ProductFilterSchema
from app.services.crud import query_products
from app.db.database import get_db_connection
import openai
import os
import json
import re
from app.services import blind_test

router = APIRouter()
router.include_router(blind_test.router, prefix="/blind-test")
openai.api_key = os.getenv("OPENAI_API_KEY")


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


@router.post("/recommendations/basic/")
async def get_basic_recommendations(
    raw_filters: ProductFilterSchema = Body(...)
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
async def get_premium_recommendations(user_input: str, previous_filled_data: dict = None):
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
