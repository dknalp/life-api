from fastapi import APIRouter, HTTPException  # APIRouter = mini-app for one feature. HTTPException = send error responses
from pydantic import BaseModel               # BaseModel lets us define the shape of data we expect from the user
from database import get_connection          # import our connection function from database.py

# create the router for goals
# this works exactly like "app" in main.py but lives in its own file
router = APIRouter()


# this class defines what data the user must send when creating a goal
# title: str      → required, must be a string
# description: str = None  → optional, defaults to None if not sent
# FastAPI validates this automatically before your function runs
class GoalCreate(BaseModel):
    title: str
    description: str = None


# --- GET /goals ---
# this endpoint returns all goals from the database
@router.get("/goals")
def get_goals():
    conn = get_connection()   # open a connection (like logging in to postgres)
    cur = conn.cursor()       # create a cursor — the tool that sends SQL through the connection

    # send this SQL to PostgreSQL
    # nothing comes back yet — results sit on the server side until we fetch them
    cur.execute("SELECT id, title, description, is_done, created_at FROM goals ORDER BY created_at DESC")

    rows = cur.fetchall()  # pull ALL result rows into Python as a list of tuples
                           # each tuple is one row, e.g: (1, "Learn SQL", "desc", False, datetime)

    cur.close()   # always close cursor when done — frees server resources
    conn.close()  # always close connection when done

    # convert list of tuples into list of dicts so the JSON looks clean
    # this is a list comprehension — a compact loop that builds a new list
    # row[0] = id, row[1] = title, row[2] = description, row[3] = is_done, row[4] = created_at
    goals = [
        {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "is_done": row[3],
            "created_at": row[4]
        }
        for row in rows
    ]

    # FastAPI automatically converts this dict to JSON and sends it as the HTTP response
    return {"goals": goals}


# --- POST /goals ---
# this endpoint creates a new goal
# "goal: GoalCreate" tells FastAPI: expect a JSON body matching GoalCreate shape, pass it in as "goal"
@router.post("/goals")
def create_goal(goal: GoalCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        # %s are placeholders — values are passed separately, never as string concatenation
        # this is how you prevent SQL injection — always use %s, never use + or f-strings for SQL
        # RETURNING id, created_at → tells PostgreSQL to send back the new row's data right after inserting
        # without RETURNING we'd need a second query just to get the new id
        "INSERT INTO goals (title, description) VALUES (%s, %s) RETURNING id, created_at",
        (goal.title, goal.description)  # these values replace the two %s placeholders, in order
    )

    # fetchone() gets exactly one row — the RETURNING result
    # we unpack the tuple directly into two variables
    new_id, created_at = cur.fetchone()

    conn.commit()  # IMPORTANT: permanently saves the INSERT
                   # without commit(), the change is held in a temporary state
                   # and thrown away when the connection closes
    cur.close()
    conn.close()

    return {"id": new_id, "title": goal.title, "description": goal.description, "created_at": created_at}


# --- PATCH /goals/{goal_id}/done ---
# PATCH means "partially update" — we're only changing is_done, not the whole row
# {goal_id} in the URL is a path parameter — FastAPI extracts it and passes it to the function
# the ": int" means FastAPI also converts it to an integer — /goals/abc/done would be rejected automatically
@router.patch("/goals/{goal_id}/done")
def complete_goal(goal_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("UPDATE goals SET is_done = TRUE WHERE id = %s", (goal_id,))

    # rowcount = how many rows were affected by the last execute()
    # if 0, no row with that id existed
    updated = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    if updated == 0:
        # raise HTTPException stops the function and sends an error response
        # 404 is the standard HTTP code for "not found"
        # the client receives: {"detail": "Goal not found"}
        raise HTTPException(status_code=404, detail="Goal not found")

    return {"message": f"Goal {goal_id} marked as done"}


# --- DELETE /goals/{goal_id} ---
# deletes a goal by id — same pattern as PATCH but runs DELETE sql
@router.delete("/goals/{goal_id}")
def delete_goal(goal_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM goals WHERE id = %s", (goal_id,))
    deleted = cur.rowcount  # 0 means no row with that id existed

    conn.commit()
    cur.close()
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Goal not found")

    return {"message": f"Goal {goal_id} deleted"}