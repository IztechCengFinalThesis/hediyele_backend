from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from app.schemas.schemas import ProductFilterSchema
from app.services.crud import query_products
from app.db.database import get_db_connection
import openai
import os
import json
import re

router = APIRouter()

openai.api_key = os.getenv("OPENAI_API_KEY")

@router.post("/products/")
async def get_products(filters: ProductFilterSchema):
    try:
        validated_filters = filters.model_dump()
        return query_products(validated_filters)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())

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
        return {"status": "error", "message": str(e)}

@router.post("/chatgpt-fill/")
async def chatgpt_fill(user_input: str, previous_filled_data: dict = None):
    if previous_filled_data:
        filter_dict = previous_filled_data
    else:
        empty_filters = ProductFilterSchema()
        filter_dict = empty_filters.model_dump()

    prompt = f"""
    Kullanıcıdan şu giriş alındı: {user_input}
    Mevcut doldurulmuş tablo:
    {json.dumps(filter_dict, indent=4)}

    Bu tabloyu kullanıcı bilgisine göre **güncelle** ve sadece eksik bilgileri tamamla.
    Daha önce doldurulmuş bilgileri değiştirme.
    **Boolean değişkenleri True veya False olarak döndür. Null kullanma.**
    JSON formatında sadece güncellenmiş tabloyu döndür.
    """

    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Sen bir asistan olarak kullanıcı girdisine göre tabloyu tamamlıyorsun. Daha önce doldurulmuş bilgileri değiştirme. JSON formatında sadece tabloyu döndür. Boolean değişkenleri True veya False olarak döndür."},
                {"role": "user", "content": prompt}
            ]
        )

        raw_content = response.choices[0].message.content.strip()
        print("🔹 OpenAI Yanıtı:", raw_content)

        cleaned_content = re.sub(r"```json\n(.*?)\n```", r"\1", raw_content, flags=re.DOTALL).strip()

        try:
            updated_data = json.loads(cleaned_content)
        except json.JSONDecodeError:
            return {
                "error": "Yanıt JSON formatında değil. OpenAI'den gelen temizlenmiş yanıt:",
                "raw_response": cleaned_content
            }

        for key, value in filter_dict.items():
            if key not in updated_data or updated_data[key] is None:
                updated_data[key] = value

        filled_filters = ProductFilterSchema(**updated_data)

        missing_fields = []
        if not any([filled_filters.age_0_2, filled_filters.age_3_5, filled_filters.age_6_12,
                    filled_filters.age_13_18, filled_filters.age_19_29, filled_filters.age_30_45,
                    filled_filters.age_45_65, filled_filters.age_65_plus]):
            missing_fields.append("Yaş aralığını belirtir misiniz?")

        if not (filled_filters.gender_male or filled_filters.gender_female):
            missing_fields.append("Hediye alacağınız kişinin cinsiyeti nedir?")

        if not any([filled_filters.special_birthday, filled_filters.special_anniversary, filled_filters.special_valentines,
                    filled_filters.special_new_year, filled_filters.special_house_warming, filled_filters.special_mothers_day,
                    filled_filters.special_fathers_day]):
            missing_fields.append("Bu hediye özel bir gün için mi? (Doğum günü, yıl dönümü vb.)")

        interest_fields = [
            filled_filters.interest_sports, filled_filters.interest_music, filled_filters.interest_books,
            filled_filters.interest_technology, filled_filters.interest_travel, filled_filters.interest_art,
            filled_filters.interest_food, filled_filters.interest_fitness, filled_filters.interest_health,
            filled_filters.interest_photography, filled_filters.interest_fashion, filled_filters.interest_pets,
            filled_filters.interest_home_decor, filled_filters.interest_movies_tv
        ]
        if not any(interest_fields):
            missing_fields.append("Kişinin ilgi alanlarından birkaçını paylaşır mısınız? (Örneğin, spor, müzik, teknoloji vb.)")

        if missing_fields:
            return {
                "message": "Daha fazla detay verebilir misiniz? " + " ".join(missing_fields),
                "filled_table": updated_data,
                "next_prompt": "Lütfen eksik bilgileri tamamlayarak tekrar deneyin."
            }

        product_recommendations = await get_products(filled_filters)

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

    except Exception as e:
        return {"error": f"Hata oluştu: {str(e)}"}
