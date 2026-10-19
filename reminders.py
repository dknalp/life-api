from fastapi import APIRouter, HTTPException  # APIRouter for this feature, HTTPException for error responses
from pydantic import BaseModel               # defines the shape of incoming data
from datetime import datetime                # needed for remind_at timestamp
from database import get_connection          # shared connection function

router = APIRouter()


# data the user sends when creating a reminder
# title: what to remind — required
# remind_at: when to remind — required, must be a datetime e.g. "2024-01-20T09:00:00"
class ReminderCreate(BaseModel):
    title: str
    remind_at: datetime


# --- GET /reminders ---
# returns all reminders, soonest first
# is_sent=False ones are still pending, is_sent=True ones already fired
@router.get("/reminders")
def get_reminders():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, title, remind_at, is_sent, created_at FROM reminders ORDER BY remind_at ASC")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    reminders = [
        {
            "id": row[0],
            "title": row[1],
            "remind_at": row[2],
            "is_sent": row[3],  # False = still pending, True = already sent
            "created_at": row[4]
        }
        for row in rows
    ]
    return {"reminders": reminders}


# --- GET /reminders/pending ---
# returns only reminders that haven't been sent yet
# useful to check what's coming up
@router.get("/reminders/pending")
def get_pending_reminders():
    conn = get_connection()
    cur = conn.cursor()

    # NOW() = current timestamp in PostgreSQL
    # this gets reminders that are in the future AND not yet marked as sent
    cur.execute(
        "SELECT id, title, remind_at, is_sent, created_at FROM reminders WHERE is_sent = FALSE AND remind_at > NOW() ORDER BY remind_at ASC"
    )
    rows = cur.fetchall()

    cur.close()
    conn.close()

    reminders = [
        {"id": row[0], "title": row[1], "remind_at": row[2], "is_sent": row[3], "created_at": row[4]}
        for row in rows
    ]
    return {"pending_reminders": reminders}


# --- POST /reminders ---
# creates a new reminder
@router.post("/reminders")
def create_reminder(reminder: ReminderCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO reminders (title, remind_at) VALUES (%s, %s) RETURNING id, created_at",
        (reminder.title, reminder.remind_at)
    )
    new_id, created_at = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": new_id,
        "title": reminder.title,
        "remind_at": reminder.remind_at,
        "is_sent": False,
        "created_at": created_at
    }


# --- PATCH /reminders/{id}/sent ---
# marks a reminder as sent
# call this after you've actually shown the reminder to the user
@router.patch("/reminders/{reminder_id}/sent")
def mark_sent(reminder_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("UPDATE reminders SET is_sent = TRUE WHERE id = %s", (reminder_id,))
    updated = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    if updated == 0:
        raise HTTPException(status_code=404, detail="Reminder not found")

    return {"message": f"Reminder {reminder_id} marked as sent"}


# --- DELETE /reminders/{id} ---
# deletes a reminder
@router.delete("/reminders/{reminder_id}")
def delete_reminder(reminder_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM reminders WHERE id = %s", (reminder_id,))
    deleted = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Reminder not found")

    return {"message": f"Reminder {reminder_id} deleted"}