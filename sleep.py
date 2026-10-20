from fastapi import APIRouter, HTTPException # APIRouter for this feature, HTTPException for error responses
from pydantic import BaseModel # defines the shape of incoming data
from datetime import datetime, timezone # datetime type for slept_at and woke_at
from typing import Optional
from database import get_connection # shared connection function

router = APIRouter()


def resolve_time(value):
    """'now' means the current UTC time; anything else is parsed as a datetime."""
    if isinstance(value, str) and value.strip().lower() == "now":
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"not a datetime or 'now': {value}")


# data the user sends when logging sleep
# slept_at: when they went to sleep — required. a datetime, or the word "now"
# woke_at: when they woke up — optional (maybe they're logging before waking)
# notes: anything extra like "had bad dreams" — optional
class SleepCreate(BaseModel):
    slept_at: str  # e.g. "2026-10-19T23:30:00" or "now"
    woke_at: Optional[str] = None  # optional datetime, or "now"
    notes: str = None  # optional


# data the user sends when they wake up (updating an existing log)
class SleepWakeUp(BaseModel):
    woke_at: str  # a datetime, or the word "now"


# --- GET /sleep ---
# returns all sleep logs, newest first
@router.get("/sleep")
def get_sleep_logs():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, slept_at, woke_at, notes, created_at FROM sleep_logs ORDER BY slept_at DESC")
    rows = cur.fetchall() # list of tuples

    cur.close()
    conn.close()

    logs = [
        {
            "id": row[0],
            "slept_at": row[1],
            "woke_at": row[2], # will be None if not set yet
            "notes": row[3],
            "created_at": row[4]
        }
        for row in rows
    ]
    return {"sleep_logs": logs}


# --- POST /sleep ---
# logs a new sleep entry
@router.post("/sleep")
def log_sleep(sleep: SleepCreate):
    conn = get_connection()
    cur = conn.cursor()

    slept_at = resolve_time(sleep.slept_at)
    woke_at = resolve_time(sleep.woke_at) if sleep.woke_at else None

    cur.execute(
        # %s placeholders keep it safe from SQL injection
        # RETURNING gets back the new row's id and created_at without a second query
        "INSERT INTO sleep_logs (slept_at, woke_at, notes) VALUES (%s, %s, %s) RETURNING id, created_at",
        (slept_at, woke_at, sleep.notes)
    )
    new_id, created_at = cur.fetchone()

    conn.commit() # save permanently
    cur.close()
    conn.close()

    return {
        "id": new_id,
        "slept_at": slept_at,
        "woke_at": woke_at,
        "notes": sleep.notes,
        "created_at": created_at
    }


# --- PATCH /sleep/{id}/wakeup ---
# updates an existing sleep log with the wake-up time
# useful when you log sleep at night and then log wake time in the morning
@router.patch("/sleep/{log_id}/wakeup")
def set_wakeup(log_id: int, data: SleepWakeUp): # log_id from URL, data from request body
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE sleep_logs SET woke_at = %s WHERE id = %s",
        (resolve_time(data.woke_at), log_id)
    )
    updated = cur.rowcount # 0 = that id didn't exist

    conn.commit()
    cur.close()
    conn.close()

    if updated == 0:
        raise HTTPException(status_code=404, detail="Sleep log not found")

    return {"message": f"Wake-up time set for log {log_id}"}


# --- DELETE /sleep/{id} ---
# deletes a sleep log
@router.delete("/sleep/{log_id}")
def delete_sleep_log(log_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM sleep_logs WHERE id = %s", (log_id,))
    deleted = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Sleep log not found")

    return {"message": f"Sleep log {log_id} deleted"}
