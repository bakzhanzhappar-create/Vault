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


def check_uuid(uuid_code:str) -> UUID | None:
    try:
        checked_uuid=UUID(uuid_code)
    except ValueError:
        print("Ошибка, гдето заляпали")
        return None
    return checked_uuid


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


def insert_table(dict_secret:dict):
    title = dict_secret.get("title")
    secret = dict_secret.get("secret")
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO test_table(title, secret) VALUES (%s, %s)""",
            (title, secret),)
            conn.commit()
    return True


def show_table():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""SELECT session_id, title, secret FROM test_table;""")
            return cursor.fetchall()


def get_secret_by_id(uuid_code:str):
    checked_uuid=check_uuid(uuid_code)
    if checked_uuid is None:
        return False
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""SELECT title, secret FROM test_table WHERE session_id = %s;""", (checked_uuid,))
            return cursor.fetchone()


def update_by_id(uuid_code: str, dict_secret:dict) -> bool:
    title = dict_secret.get("title")
    secret = dict_secret.get("secret")
    checked_uuid = check_uuid(uuid_code)
    if checked_uuid is None:
        return False
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""UPDATE test_table SET title = %s, secret = %s WHERE session_id = %s;""", (title, secret, checked_uuid),)
            conn.commit()
            return cursor.rowcount == 1


def delete_by_id(uuid_code:str) -> bool:
    checked_uuid = check_uuid(uuid_code)
    if checked_uuid is None:
        return False
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""DELETE FROM test_table WHERE session_id = %s;""", (checked_uuid,),)
            conn.commit()
            return cursor.rowcount == 1