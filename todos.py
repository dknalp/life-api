from fastapi import APIRouter, HTTPException  # same imports as goals.py — every feature file needs these
from pydantic import BaseModel               # for defining the shape of incoming data
from database import get_connection          # our shared connection function

router = APIRouter()  # create the router for todos — gets plugged into main.py with include_router()


# todos only need a title — no description like goals
class TodoCreate(BaseModel):
    title: str  # required, must be a string


# --- GET /todos ---
# returns all todos, newest first
@router.get("/todos")
def get_todos():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, title, is_done, created_at FROM todos ORDER BY created_at DESC")

    rows = cur.fetchall()  # list of tuples: [(1, "buy milk", False, datetime), ...]

    cur.close()
    conn.close()

    # convert tuples to dicts — row[0]=id, row[1]=title, row[2]=is_done, row[3]=created_at
    todos = [
        {"id": row[0], "title": row[1], "is_done": row[2], "created_at": row[3]}
        for row in rows
    ]
    return {"todos": todos}


# --- POST /todos ---
# creates a new todo and returns the created row
@router.post("/todos")
def create_todo(todo: TodoCreate):
    conn = get_connection()
    cur = conn.cursor()

    # %s placeholder for the title value — safe from SQL injection
    # RETURNING id, created_at → get the new row's data back without a second query
    cur.execute(
        "INSERT INTO todos (title) VALUES (%s) RETURNING id, created_at",
        (todo.title,)  # note the trailing comma — this makes it a tuple, not just parentheses
    )

    new_id, created_at = cur.fetchone()  # unpack the one returned row into two variables

    conn.commit()  # save the INSERT permanently
    cur.close()
    conn.close()

    # is_done is always False for a new todo — no need to fetch it from db
    return {"id": new_id, "title": todo.title, "is_done": False, "created_at": created_at}


# --- PATCH /todos/{todo_id}/done ---
# marks a todo as done — only changes is_done, nothing else
@router.patch("/todos/{todo_id}/done")
def complete_todo(todo_id: int):  # todo_id comes from the URL — FastAPI extracts and converts it to int
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("UPDATE todos SET is_done = TRUE WHERE id = %s", (todo_id,))
    updated = cur.rowcount  # how many rows were changed — 0 means that id didn't exist

    conn.commit()
    cur.close()
    conn.close()

    if updated == 0:
        raise HTTPException(status_code=404, detail="Todo not found")  # stop and send error response

    return {"message": f"Todo {todo_id} marked as done"}


# --- DELETE /todos/{todo_id} ---
# deletes a todo permanently
@router.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM todos WHERE id = %s", (todo_id,))
    deleted = cur.rowcount  # 0 = that id didn't exist

    conn.commit()
    cur.close()
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Todo not found")

    return {"message": f"Todo {todo_id} deleted"}