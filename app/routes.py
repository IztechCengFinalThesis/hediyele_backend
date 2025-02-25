from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from schemas import ProductFilterSchema
from crud import query_products
from database import get_db_connection

router = APIRouter()

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
