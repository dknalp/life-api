from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_connection

router = APIRouter()

# title: short label — required
# body: longer description or notes — optional
class IdeaCreate(BaseModel):
    title: str
    body: str = None

# --- GET /ideas ---
@router.get("/ideas")
def get_ideas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, body, created_at FROM ideas ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return {"ideas": [
        {"id": r[0], "title": r[1], "body": r[2], "created_at": r[3]}
        for r in rows
    ]}

# --- POST /ideas ---
@router.post("/ideas")
def create_idea(idea: IdeaCreate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO ideas (title, body) VALUES (%s, %s) RETURNING id, created_at",
        (idea.title, idea.body)
    )
    new_id, created_at = cur.fetchone()
    conn.commit(); cur.close(); conn.close()
    return {"id": new_id, "title": idea.title, "body": idea.body, "created_at": created_at}

# --- DELETE /ideas/{id} ---
@router.delete("/ideas/{idea_id}")
def delete_idea(idea_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM ideas WHERE id = %s", (idea_id,))
    deleted = cur.rowcount
    conn.commit(); cur.close(); conn.close()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Idea not found")
    return {"message": f"Idea {idea_id} deleted"}
