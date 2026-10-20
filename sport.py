from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import date
from database import get_connection

router = APIRouter()

# data the user sends when logging a sport day
# activity: what they did — required, e.g. "run"
# done_on: which day — required
# duration_minutes: how long it lasted — optional
# notes: anything extra — optional
class SportCreate(BaseModel):
    activity: str
    done_on: date  # e.g. "2026-10-20"
    duration_minutes: int = None  # optional
    notes: str = None  # optional

# --- GET /sport ---
# returns all sport days, newest first
@router.get("/sport")
def get_sport_days():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, activity, done_on, duration_minutes, notes, created_at FROM sport_days ORDER BY done_on DESC")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    days = [
        {
            "id": row[0],
            "activity": row[1],
            "done_on": row[2],
            "duration_minutes": row[3],  # None if not set
            "notes": row[4],
            "created_at": row[5]
        }
        for row in rows
    ]
    return {"sport_days": days}

# --- POST /sport ---
# logs a new sport day
@router.post("/sport")
def log_sport_day(sport: SportCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        # %s placeholders keep it safe from SQL injection
        # RETURNING gets back the new row's id and created_at without a second query
        "INSERT INTO sport_days (activity, done_on, duration_minutes, notes) VALUES (%s, %s, %s, %s) RETURNING id, created_at",
        (sport.activity, sport.done_on, sport.duration_minutes, sport.notes)
    )
    new_id, created_at = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": new_id,
        "activity": sport.activity,
        "done_on": sport.done_on,
        "duration_minutes": sport.duration_minutes,
        "notes": sport.notes,
        "created_at": created_at
    }

# --- DELETE /sport/{id} ---
# deletes a sport day
@router.delete("/sport/{day_id}")
def delete_sport_day(day_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM sport_days WHERE id = %s", (day_id,))
    deleted = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Sport day not found")

    return {"message": f"Sport day {day_id} deleted"}
