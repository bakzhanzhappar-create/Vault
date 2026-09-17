import os
import psycopg
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    dbname=os.getenv("DB_NAME", "vault_db"),
    user=os.getenv("DB_USER", "vault_app"),
    password=os.getenv("DB_PASSWORD"),
    )


def create_test_table():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_table(
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title JSON NOT NULL,
                secret JSON,
                user_id JSON NOT NULL
            );
            """)
            conn.commit()
    return True


def insert_table(title_name:str, secret_text: str, id_user:str):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO test_table(title, secret, user_id) VALUES (%s, %s, %s)""",
            (title_name, secret_text, id_user),)
            conn.commit()
    return True

def show_table():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""SELECT * FROM test_table;""")
            print(cursor.fetchall())