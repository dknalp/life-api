from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from database import get_connection

router = APIRouter()

# description: what was eaten — required
# meal_type: breakfast / lunch / dinner / snack — optional
# calories: rough number — optional
# eaten_at: defaults to now if not sent
class EatingCreate(BaseModel):
    description: str
    meal_type: str = None
    calories: int = None
    eaten_at: datetime = None  # if omitted the DB default (NOW()) is used

# --- GET /eatings ---
@router.get("/eatings")
def get_eatings():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, description, meal_type, calories, eaten_at, created_at FROM eatings ORDER BY eaten_at DESC")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return {"eatings": [
        {"id": r[0], "description": r[1], "meal_type": r[2], "calories": r[3],
         "eaten_at": r[4], "created_at": r[5]}
        for r in rows
    ]}

# --- POST /eatings ---
@router.post("/eatings")
def log_eating(eating: EatingCreate):
    conn = get_connection()
    cur = conn.cursor()
    if eating.eaten_at:
        cur.execute(
            "INSERT INTO eatings (description, meal_type, calories, eaten_at) VALUES (%s, %s, %s, %s) RETURNING id, eaten_at, created_at",
            (eating.description, eating.meal_type, eating.calories, eating.eaten_at)
        )
    else:
        cur.execute(
            "INSERT INTO eatings (description, meal_type, calories) VALUES (%s, %s, %s) RETURNING id, eaten_at, created_at",
            (eating.description, eating.meal_type, eating.calories)
        )
    new_id, eaten_at, created_at = cur.fetchone()
    conn.commit(); cur.close(); conn.close()
    return {"id": new_id, "description": eating.description, "meal_type": eating.meal_type,
            "calories": eating.calories, "eaten_at": eaten_at, "created_at": created_at}

# --- DELETE /eatings/{id} ---
@router.delete("/eatings/{eating_id}")
def delete_eating(eating_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM eatings WHERE id = %s", (eating_id,))
    deleted = cur.rowcount
    conn.commit(); cur.close(); conn.close()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Eating not found")
    return {"message": f"Eating {eating_id} deleted"}
