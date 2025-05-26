from app.db.database import get_db_connection
from fastapi import HTTPException
from typing import Dict

def query_products(filters: Dict[str, bool]):
    conn = get_db_connection()
    cur = conn.cursor()

    weights = {
        "age_0_2": 2.0,
        "age_3_5": 2.0,
        "age_6_12": 2.0,
        "age_13_18": 2.0,
        "age_19_29": 2.0,
        "age_30_45": 2.0,
        "age_45_65": 2.0,
        "age_65_plus": 2.0,
        "gender_male": 4.0,
        "gender_female": 4.0,
        "special_birthday": 1.0,
        "special_anniversary": 1.0,
        "special_valentines": 1.0,
        "special_new_year": 1.0,
        "special_house_warming": 1.0,
        "special_mothers_day": 1.0,
        "special_fathers_day": 1.0,
        "interest_sports": 1.0,
        "interest_music": 1.0,
        "interest_books": 1.0,
        "interest_technology": 1.0,
        "interest_travel": 1.0,
        "interest_art": 1.0,
        "interest_food": 1.0,
        "interest_fitness": 1.0,
        "interest_health": 1.0,
        "interest_photography": 1.0,
        "interest_fashion": 1.0,
        "interest_pets": 1.0,
        "interest_home_decor": 1.0,
        "interest_movies_tv": 1.0
    }

    NORMALIZE = 10.0
    expression_parts = []

    for key, value in filters.items():
        if key in weights and value:
            weight = weights.get(key, 1.0)
            expression_parts.append(f"{weight} * POWER((COALESCE({key}, 0)/{NORMALIZE}) - 1, 2)")

    if not expression_parts:
        return {"message": "No filters selected", "products": []}

    diff_sum = " + ".join(expression_parts)
    score_expr = f"(1 / (1 + SQRT({diff_sum})))"

    price_clause = ""
    if "min_budget" in filters and filters["min_budget"] is not None:
        price_clause += f" AND p.price >= {filters['min_budget']}"
    if "max_budget" in filters and filters["max_budget"] is not None:
        price_clause += f" AND p.price <= {filters['max_budget']}"

    query = f"""
        SELECT p.id, p.product_name, p.price, p.site, p.link, ({score_expr}) AS score, is_last_7_days_lower_price, is_last_30_days_lower_price
        FROM product p
        JOIN product_features pf ON p.product_features_id = pf.id
        WHERE 1=1 {price_clause}
        ORDER BY score DESC
        LIMIT 10
    """

    try:
        cur.execute(query)
        products = cur.fetchall()
        return {
            "products": [
                {
                    "id": row[0],
                    "name": row[1], 
                    "price": float(row[2]) if row[2] is not None else 0.0, 
                    "site": row[3] if row[3] is not None else "",
                    "link": row[4] if row[4] is not None else "",
                    "score": float(row[5]) if row[5] is not None else 0.0,
                    "is_last_7_days_lower_price": row[6],
                    "is_last_30_days_lower_price": row[7]
                } for row in products
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
