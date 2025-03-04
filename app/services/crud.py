from app.db.database import get_db_connection
from fastapi import HTTPException
from typing import Dict

def query_products(filters: Dict[str, bool]):

    conn = get_db_connection()
    cur = conn.cursor()

    active_filters = [key for key, value in filters.items() if value]

    if not active_filters:
        return {"message": "No filters selected", "products": []}

    filter_expression = " * ".join(active_filters)

    query = f"""
        SELECT p.product_name, pf.product_score
        FROM product p
        JOIN (
            SELECT id, ({filter_expression}) AS product_score
            FROM product_features
            ORDER BY product_score DESC
            LIMIT 10
        ) AS pf ON p.id = pf.id;
    """ 

    try:
        cur.execute(query)
        products = cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

    return {"products": products}
