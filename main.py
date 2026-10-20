from fastapi import FastAPI

from goals import router as goals_router
from todos import router as todos_router
from sleep import router as sleep_router
from diary import router as diary_router
from reminders import router as reminders_router
from sport import router as sport_router
from eatings import router as eatings_router
from steps import router as steps_router
from ideas import router as ideas_router

app = FastAPI(title="Life API")

# plug every feature router into the main app
# each line here makes that feature's endpoints visible at /docs
app.include_router(goals_router)
app.include_router(todos_router)
app.include_router(sleep_router)
app.include_router(diary_router)
app.include_router(reminders_router)
app.include_router(sport_router)
app.include_router(eatings_router)
app.include_router(steps_router)
app.include_router(ideas_router)


# health check — visiting http://localhost:8000/ returns this
@app.get("/")
def root():
    return {"message": "Life API is running. For docs : GET /docs"}
