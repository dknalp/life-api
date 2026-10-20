# life-api

A small FastAPI server for tracking goals, todos, sleep, diary entries, reminders and sport days. The data lives in PostgreSQL.

## Run it

Connection settings come from the environment (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`), read in `database.py`. Defaults are in `.env.example`.

The `sport_days` table is in `schema.sql`. The other tables were created outside this repo and are assumed to already exist.

```bash
psql "$DB_NAME" -f schema.sql
```

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Docs are at http://localhost:8000/docs.

## Docker

```bash
docker build -t life-api .
docker run -d --name life-api -p 8000:8000 life-api
```

## Client

`client.py` is a small terminal client. With it on your `PATH` as `life-api-client`:

```bash
life-api-client
```
