import os
import psycopg2  # the library that lets Python talk to PostgreSQL


def get_connection():
    # reads connection settings from environment variables
    # set them in docker-compose.yml or in a .env file — never hardcode credentials
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "life"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", ""),
    )
