from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import date
from database import get_connection

router = APIRouter()

# title: e.g. "Dad's birthday", "Partner anniversary" — required
# occasion_date: full date (year = birth/event year) — required
# category: birthday | anniversary | other — required
# person: whose date — optional
class SpecialDateCreate(BaseModel):
    title: str
    occasion_date: date  # e.g. "1990-05-15"
    category: str        # birthday | anniversary | other
    person: str = None

# --- GET /special-dates ---
# ordered so the soonest upcoming date comes first regardless of year
@router.get("/special-dates")
def get_special_dates():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, occasion_date, category, person, created_at,
               (EXTRACT(DOY FROM occasion_date)::int + 365
                - EXTRACT(DOY FROM NOW())::int) % 365 AS days_away
        FROM special_dates
        ORDER BY days_away
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return {"special_dates": [
        {"id": r[0], "title": r[1], "occasion_date": r[2], "category": r[3],
         "person": r[4], "created_at": r[5], "days_until_next": r[6]}
        for r in rows
    ]}

# --- POST /special-dates ---
@router.post("/special-dates")
def create_special_date(data: SpecialDateCreate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO special_dates (title, occasion_date, category, person) VALUES (%s, %s, %s, %s) RETURNING id, created_at",
        (data.title, data.occasion_date, data.category, data.person)
    )
    new_id, created_at = cur.fetchone()
    conn.commit(); cur.close(); conn.close()
    return {"id": new_id, "title": data.title, "occasion_date": data.occasion_date,
            "category": data.category, "person": data.person, "created_at": created_at}

# --- DELETE /special-dates/{id} ---
@router.delete("/special-dates/{date_id}")
def delete_special_date(date_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM special_dates WHERE id = %s", (date_id,))
    deleted = cur.rowcount
    conn.commit(); cur.close(); conn.close()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Special date not found")
    return {"message": f"Special date {date_id} deleted"}
