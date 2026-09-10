import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

with psycopg.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    dbname=os.getenv("DB_NAME", "vault_db"),
    user=os.getenv("DB_USER", "vault_app"),
    password=os.getenv("DB_PASSWORD"),) as conn:

    with conn.cursor() as cursor:

        cursor.execute("SELECT current_user;")
        print("Connected as:", cursor.fetchone()[0])

        cursor.execute("""
        CREATE TEMP TABLE test(
        id SERIAL PRIMARY KEY,
        something TEXT,
        number INTEGER)
        """)

        cursor.execute("INSERT INTO test(something, number) VALUES ('niggadeluxe', 255)")

        cursor.execute("SELECT * FROM test")

        print(cursor.fetchone())


cursor.close()
conn.close()