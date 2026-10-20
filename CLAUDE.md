# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A small FastAPI server that stores personal tracking data in PostgreSQL: goals, todos, sleep logs, diary entries, and reminders. There is no ORM, no migrations folder, and no test suite. Each feature is one file that opens a raw `psycopg2` connection, runs SQL, and closes it.

## Commands

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Interactive docs: http://localhost:8000/docs. Health check: `GET /` returns `{"message": "Life API is running. For docs : GET /docs"}`.

Connection settings come from the environment, read in `database.py`. Defaults are host `127.0.0.1`, port `5432`, database `life`, user `postgres`, empty password. Copy `.env.example` (host `192.168.0.115`) and export the variables, or pass them through docker-compose:

```bash
docker compose up --build
# or
docker build -t life-api .
docker run -d --name life-api -p 8000:8000 --env-file .env life-api
```

The image is Python 3.12 and copies only the server modules. `client.py` is in `.dockerignore` and is not in the image.

Terminal client (uses `requests`, which is not in `requirements.txt`):

```bash
python3 client.py
```

`BASE` at the top of `client.py` is the server URL. Strings must be quoted and ids must be bare numbers; `help` lists commands, `q` quits.

There is no linter, formatter, or test runner configured. Nothing to run for a single test.

## Architecture

`main.py` builds the FastAPI app and mounts five routers. Adding a feature means a new module with an `APIRouter`, then one `include_router` line in `main.py`, plus a `COPY` line in the `Dockerfile`.

`database.py` is the only shared piece: `get_connection()` reads `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`. Every handler calls it, uses a cursor, and closes both cursor and connection itself. Writes call `conn.commit()`. There is no pool and no transaction helper.

Each router follows the same shape: a Pydantic `BaseModel` for the body, a list endpoint that returns `{"<plural>": [...]}`, a create that `RETURNING`s `id` and `created_at`, and a delete that 404s when `rowcount` is 0. Rows are mapped by column index, not by name. Missing rows raise `HTTPException(404)`.

Endpoints and the tables they hit:

| Module | Routes | Table |
|---|---|---|
| `goals.py` | `GET/POST /goals`, `PATCH /goals/{id}/done`, `DELETE /goals/{id}` | `goals` (title, description, is_done) |
| `todos.py` | `GET/POST /todos`, `PATCH /todos/{id}/done`, `DELETE /todos/{id}` | `todos` (title, is_done) |
| `sleep.py` | `GET/POST /sleep`, `PATCH /sleep/{id}/wakeup`, `DELETE /sleep/{id}` | `sleep_logs` (slept_at, woke_at, notes) |
| `diary.py` | `GET/POST /diary`, `GET /diary/{id}`, `PATCH /diary/{id}`, `DELETE /diary/{id}` | `diary` (title, body) |
| `reminders.py` | `GET/POST /reminders`, `GET /reminders/pending`, `PATCH /reminders/{id}/sent`, `DELETE /reminders/{id}` | `reminders` (title, remind_at, is_sent) |
| `sport.py` | `GET/POST /sport`, `DELETE /sport/{id}` | `sport_days` (activity, done_on, duration_minutes, notes) |
| `eatings.py` | `GET/POST /eatings`, `DELETE /eatings/{id}` | `eatings` (description, meal_type, calories, eaten_at) |
| `steps.py` | `GET/POST /steps`, `DELETE /steps/{id}` | `step_logs` (steps, recorded_on, notes) |
| `ideas.py` | `GET/POST /ideas`, `DELETE /ideas/{id}` | `ideas` (title, body) |
| `special_dates.py` | `GET/POST /special-dates`, `DELETE /special-dates/{id}` | `special_dates` (title, occasion_date, category, person) |

Two places diverge from that pattern:

- `PATCH /diary/{id}` builds the `SET` clause from whichever of `title` and `body` was sent. Column names come from a fixed dict of those two fields, then values are bound with `%s`. An empty body is a 400.
- `GET /reminders/pending` filters `is_sent = FALSE AND remind_at > NOW()`. Nothing in this repo sends reminders; `PATCH /reminders/{id}/sent` only flips the flag after something else has shown it.

`schema.sql` defines `sport_days`, `eatings`, `step_logs`, `ideas`, and `special_dates`. Apply once with `psql "$DB_NAME" -f schema.sql`. The older tables (goals, todos, sleep_logs, diary, reminders) are assumed to already exist with the columns the `SELECT` lists (`id`, `created_at`, plus the fields above). `is_done` and `is_sent` default to false in the database; inserts never set them.

`client.py` is a REPL, not part of the server. It parses a line with `shlex`, then dispatches by command shape: no-arg `list`, one quoted string (`todos/goals/diary/sleep add`), two quoted strings (`reminders add`), one bare id (done/delete/sent), or id plus quoted timestamp (`sleep wakeup`). It prints the status code and JSON. It does not cover `GET /diary/{id}`, `PATCH /diary/{id}`, `GET /reminders/pending`, or optional fields like `duration_minutes`, `calories`, `meal_type`. `steps add` and `special-dates add` take two and three quoted strings respectively.
