from fastapi import APIRouter, HTTPException  # APIRouter for this feature, HTTPException for error responses
from pydantic import BaseModel               # defines the shape of incoming data
from database import get_connection          # shared connection function

router = APIRouter()


# data the user sends when creating a diary entry
# title: optional — sometimes you just want to write without a title
# body: required — the actual content of the entry
class DiaryCreate(BaseModel):
    title: str = None  # optional
    body: str          # required


# data the user sends when editing an entry
# both fields optional — user might only want to change the title or only the body
class DiaryUpdate(BaseModel):
    title: str = None
    body: str = None


# --- GET /diary ---
# returns all diary entries, newest first
@router.get("/diary")
def get_entries():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, title, body, created_at FROM diary ORDER BY created_at DESC")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    entries = [
        {"id": row[0], "title": row[1], "body": row[2], "created_at": row[3]}
        for row in rows
    ]
    return {"entries": entries}


# --- GET /diary/{id} ---
# returns one specific diary entry by id
# useful when you want to read a full entry
@router.get("/diary/{entry_id}")
def get_entry(entry_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, title, body, created_at FROM diary WHERE id = %s", (entry_id,))
    row = cur.fetchone()  # fetchone because we expect exactly one row (or None if not found)

    cur.close()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {"id": row[0], "title": row[1], "body": row[2], "created_at": row[3]}


# --- POST /diary ---
# creates a new diary entry
@router.post("/diary")
def create_entry(entry: DiaryCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO diary (title, body) VALUES (%s, %s) RETURNING id, created_at",
        (entry.title, entry.body)
    )
    new_id, created_at = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return {"id": new_id, "title": entry.title, "body": entry.body, "created_at": created_at}


# --- PATCH /diary/{id} ---
# edits an existing diary entry — can update title, body, or both
@router.patch("/diary/{entry_id}")
def update_entry(entry_id: int, data: DiaryUpdate):
    # only update fields that were actually sent — don't wipe fields the user didn't mention
    # we build the SET clause dynamically based on what was provided
    fields = {}
    if data.title is not None:
        fields["title"] = data.title
    if data.body is not None:
        fields["body"] = data.body

    # if the user sent nothing to update, there's nothing to do
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    # build the SQL dynamically: "title = %s" or "title = %s, body = %s" etc.
    set_clause = ", ".join(f"{key} = %s" for key in fields)
    values = list(fields.values()) + [entry_id]  # values for the SET clause, then the WHERE id

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(f"UPDATE diary SET {set_clause} WHERE id = %s", values)
    updated = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    if updated == 0:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {"message": f"Entry {entry_id} updated"}


# --- DELETE /diary/{id} ---
# deletes a diary entry permanently
@router.delete("/diary/{entry_id}")
def delete_entry(entry_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM diary WHERE id = %s", (entry_id,))
    deleted = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {"message": f"Entry {entry_id} deleted"}