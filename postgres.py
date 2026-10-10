import os
import psycopg
from dotenv import load_dotenv
from uuid import UUID
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
                session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title VARCHAR(100) NOT NULL,
                secret TEXT
            );
            """)
            conn.commit()
    return True


def insert_table(title_name:str, secret_text: str):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO test_table(title, secret) VALUES (%s, %s)""",
            (title_name, secret_text),)
            conn.commit()
    return True


def show_table():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""SELECT session_id, title, secret FROM test_table;""")
            return cursor.fetchall()


def get_secret_by_id(uuid_code:UUID):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""SELECT title, secret FROM test_table WHERE session_id = %s;""", (uuid_code,))
            return cursor.fetchone()

# Update
def update_by_id(uuid_code: UUID, title: str, secret: str) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""UPDATE test_table SET title = %s, secret = %s WHERE session_id = %s;""", (title, secret, uuid_code),)
            conn.commit()
            return cursor.rowcount == 1

# Delete
def delete_by_id(uuid_code:UUID) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""DELETE FROM test_table WHERE session_id = %s;""", (uuid_code,),)
            conn.commit()
            return cursor.rowcount == 1