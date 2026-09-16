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

        def create_test_table():
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS test(
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title JSON NOT NULL,
            secret JSON,
            user_id JSON)
            """)
            return True

        def insert_table(title_name: str, secret_data: str, user_id: str):
            cursor.execute("""
            INSERT INTO test(title, secret, user_id) VALUES (%s, %s, %s)
                           """)
            return True

        def show_table():
            cursor.execute("SELECT * FROM test")
            print(cursor.fetchone())

        create_test_table()
cursor.close()
conn.close()