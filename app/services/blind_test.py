from typing import List, Optional
from fastapi import APIRouter, HTTPException
from app.schemas.schemas import FeatureInput, BlindTestSubmission
from app.db.database import get_db_connection

router = APIRouter()

def map_features(input: FeatureInput) -> dict:
    base_keys = [
        "age_0_2", "age_3_5", "age_6_12", "age_13_18", "age_19_29", "age_30_45", "age_45_65", "age_65_plus",
        "gender_male", "gender_female",
        "special_birthday", "special_anniversary", "special_valentines", "special_new_year",
        "special_house_warming", "special_mothers_day", "special_fathers_day",
        "interest_sports", "interest_music", "interest_books", "interest_technology",
        "interest_travel", "interest_art", "interest_food", "interest_fitness", "interest_health",
        "interest_photography", "interest_fashion", "interest_pets", "interest_home_decor", "interest_movies_tv"
    ]
    mapped = dict.fromkeys(base_keys, 0.0)
    if input.age:
        mapped[f"age_{input.age}"] = 1.0
    if input.gender:
        mapped[f"gender_{input.gender}"] = 1.0
    if input.special:
        mapped[f"special_{input.special}"] = 1.0
    for interest in input.interests:
        key = f"interest_{interest}"
        if key in mapped:
            mapped[key] = 1.0
    return mapped

def run_algorithm(
    conn,
    mapped_features: dict,
    algo: str,
    exclude_ids: List[int] = [],
    min_budget: Optional[float] = None,
    max_budget: Optional[float] = None
) -> List[dict]:
    cur = conn.cursor()

    # 1. Skor hesaplama algoritmaları
    if algo == "algo1":
        expression_parts = [
            f"(COALESCE({k}, 0) + 0.1)"
            for k, v in mapped_features.items() if v > 0
        ]
        score_expr = " * ".join(expression_parts)

    elif algo == "algo2":
        weights = {
            k: (
                1.0 if "interest" in k else
                1.0 if "special" in k else
                4.0 if "gender" in k else
                2.0
            )
            for k in mapped_features.keys()
        }
        expression_parts = [
            f"({weights[k]} * (COALESCE({k}, 0) + 0.1))"
            for k, v in mapped_features.items() if v > 0
        ]
        score_expr = " + ".join(expression_parts)

    else:  # algo3
        expression_parts = []
        for k, v in mapped_features.items():
            if v > 0:
                if "gender" in k:
                    expression_parts.append(f"(2.0 * (COALESCE({k}, 0) + 0.1))")
                elif "interest" in k:
                    expression_parts.append(f"(0.5 * (COALESCE({k}, 0) + 0.1))")
                else:
                    expression_parts.append(f"(COALESCE({k}, 0) + 0.1)")
        score_expr = " + ".join(expression_parts)

    if not expression_parts:
        return []

    # 2. Fiyat filtresi
    price_clause = ""
    if min_budget is not None:
        price_clause += f" AND p.price >= {min_budget}"
    if max_budget is not None:
        price_clause += f" AND p.price <= {max_budget}"

    # 3. Hariç tutulan ürünler
    exclude_clause = ""
    if exclude_ids:
        exclude_ids_str = ", ".join(str(i) for i in exclude_ids)
        exclude_clause = f" AND p.id NOT IN ({exclude_ids_str})"

    # 4. SQL Sorgusu
    query = f"""
        SELECT p.id, p.product_name, p.price, ({score_expr}) AS score
        FROM product p
        JOIN product_features pf ON p.product_features_id = pf.id
        WHERE 1=1 {exclude_clause} {price_clause}
        ORDER BY score DESC
        LIMIT 5
    """

    try:
        cur.execute(query)
        rows = cur.fetchall()
        return [
            {
                "product_id": r[0],
                "product_name": r[1],
                "price": float(r[2]),
                "score": float(r[3]),
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()

@router.post("/recommendations")
def get_blind_test_recommendations(features: FeatureInput):
    conn = get_db_connection()
    mapped = map_features(features)
    results = {
        "algorithm_1": run_algorithm(conn, mapped, "algo1", [], features.min_budget, features.max_budget),
        "algorithm_2": run_algorithm(conn, mapped, "algo2", [], features.min_budget, features.max_budget),
        "algorithm_3": run_algorithm(conn, mapped, "algo3", [], features.min_budget, features.max_budget),
    }
    conn.close()
    return results

@router.post("/submit")
def submit_blind_test(data: BlindTestSubmission):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO blind_test_session (parameters) VALUES (%s) RETURNING id",
            (data.session_parameters.json(),)
        )
        session_id = cur.fetchone()[0]

        for s in data.selections:
            cur.execute(
                """
                INSERT INTO blind_test_recommendations (
                    blind_test_session_id, algorithm_name, recommended_product_id,
                    is_selected, recommended_order, bad_recommendation
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (session_id, s.algorithm, s.product_id, s.is_selected, s.recommended_order, s.bad_recommendation)
            )

        conn.commit()
        return {"status": "ok", "session_id": session_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/previous-sessions")
def get_previous_sessions():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, parameters, created_at 
            FROM blind_test_session 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        rows = cur.fetchall()
        return [
            {
                "session_id": row[0],
                "parameters": row[1],
                "created_at": row[2].isoformat()
            }
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close() 