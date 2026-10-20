from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import date
from database import get_connection

router = APIRouter()

# steps: how many steps that day — required
# recorded_on: the date — required
# notes: optional extra info
class StepsCreate(BaseModel):
    steps: int
    recorded_on: date  # e.g. "2026-10-20"
    notes: str = None

# --- GET /steps ---
@router.get("/steps")
def get_steps():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, steps, recorded_on, notes, created_at FROM step_logs ORDER BY recorded_on DESC")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return {"step_logs": [
        {"id": r[0], "steps": r[1], "recorded_on": r[2], "notes": r[3], "created_at": r[4]}
        for r in rows
    ]}

# --- POST /steps ---
@router.post("/steps")
def log_steps(data: StepsCreate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO step_logs (steps, recorded_on, notes) VALUES (%s, %s, %s) RETURNING id, created_at",
        (data.steps, data.recorded_on, data.notes)
    )
    new_id, created_at = cur.fetchone()
    conn.commit(); cur.close(); conn.close()
    return {"id": new_id, "steps": data.steps, "recorded_on": data.recorded_on,
            "notes": data.notes, "created_at": created_at}

# --- DELETE /steps/{id} ---
@router.delete("/steps/{log_id}")
def delete_steps(log_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM step_logs WHERE id = %s", (log_id,))
    deleted = cur.rowcount
    conn.commit(); cur.close(); conn.close()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Step log not found")
    return {"message": f"Step log {log_id} deleted"}
