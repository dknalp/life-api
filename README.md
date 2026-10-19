# life-api

A small FastAPI server for tracking goals, todos, sleep, diary entries and reminders. The data lives in PostgreSQL.

## Run it

The API expects PostgreSQL on `192.168.0.115`, database `life`, user `postgres`. Connection settings live in `database.py`, which is not in this repo.

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
