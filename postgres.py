import os
import psycopg
import json
from psycopg.types.json import Jsonb
from dotenv import load_dotenv
from uuid import UUID
from datetime import datetime
load_dotenv()


class VaultRepository:
    def __init__(self, conninfo: str = None):
        """
        Инициализация репозитория.
        Можно передать строку подключения или брать параметры из переменных окружения.
        """
        self.conninfo = conninfo or self._build_conninfo()


    @staticmethod
    def _build_conninfo() -> str:
        """Сборка строки подключения из env-переменных"""
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        dbname = os.getenv("DB_NAME", "vault_db")
        user = os.getenv("DB_USER", "vault_app")
        password = os.getenv("DB_PASSWORD", "")
        return f"host={host} port={port} dbname={dbname} user={user} password={password}"


    def _get_connection(self):
        return psycopg.connect(self.conninfo)


    @staticmethod
    def check_uuid(uuid_code) -> UUID | None:
        if isinstance(uuid_code, UUID):
            return uuid_code
        try:
            return UUID(str(uuid_code))
        except (ValueError, TypeError):
            print("ERROR: Incorrect UUID!")
            return None


    def create_table(self) -> bool:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS vault(
                    session_id UUID PRIMARY KEY,
                    title JSONB NOT NULL,
                    secret JSONB
                );
                """)
                conn.commit()
        print("Table vault created/checked successfully!")
        return True


    def insert_table(self, session_id: UUID, dict_secret: dict) -> bool:
        title = dict_secret.get("title")
        secret = dict_secret.get("secret")
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO vault(session_id, title, secret) VALUES (%s, %s, %s)""",
                    (session_id, Jsonb(title), Jsonb(secret)),
                )
                conn.commit()
        return True


    def show_table(self):
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT session_id, title, secret FROM vault;""")
                return cursor.fetchall()


    def get_secret_by_id(self, uuid_code):
        checked_uuid = self.check_uuid(uuid_code)
        if checked_uuid is None:
            return False
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT title, secret FROM vault WHERE session_id = %s;""",
                    (checked_uuid,)
                )
                return cursor.fetchone()


    def update_by_id(self, uuid_code, dict_secret: dict) -> bool:
        title = dict_secret.get("title")
        secret = dict_secret.get("secret")
        checked_uuid = self.check_uuid(uuid_code)
        if checked_uuid is None:
            return False
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE vault SET title = %s, secret = %s WHERE session_id = %s;""",
                    (Jsonb(title), Jsonb(secret), checked_uuid),
                )
                conn.commit()
                return cursor.rowcount == 1


    def delete_by_id(self, uuid_code) -> bool:
        checked_uuid = self.check_uuid(uuid_code)
        if checked_uuid is None:
            return False
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """DELETE FROM vault WHERE session_id = %s;""",
                    (checked_uuid,)
                )
                conn.commit()
                return cursor.rowcount == 1

    def backup(self, backup_dir: str = ".") -> str | None:
        try:
            dbname = os.getenv("DB_NAME", "vault_db")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"backup_{dbname}_{timestamp}.json")

            rows = self.show_table()
            backup_data = []
            for row in rows:
                session_id, title, secret = row
                backup_data.append({
                    "session_id": str(session_id),
                    "title": title,
                    "secret": secret
                })

            with open(backup_file, "w", encoding="utf-8") as file:
                json.dump(backup_data, file, ensure_ascii=False, indent=4)

            print(f"Бэкап успешно создан: {backup_file}")
            return backup_file
        except Exception as error:
            print(f"Ошибка при создании бэкапа: {error}")
            return None


    def restore(self, backup_file: str) -> bool | None:
        if not os.path.exists(backup_file):
            print(f"Файл бэкапа не найден: {backup_file}")
            return False

        try:
            with open(backup_file, "r", encoding="utf-8") as file:
                backup_data = json.load(file)

            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""TRUNCATE TABLE vault;""")

                    for item in backup_data:
                        session_id = self.check_uuid(item["session_id"])
                        if not session_id:
                            continue

                        title = item.get("title")
                        secret = item.get("secret")

                        cursor.execute(
                            """INSERT INTO vault(session_id, title, secret)
                               VALUES (%s, %s, %s)""",
                            (session_id, Jsonb(title), Jsonb(secret)),
                        )
                    conn.commit()

            print(f"База данных успешно восстановлена из файла: {backup_file}")
            return True
        except Exception as error:
            print(f"Ошибка при восстановлении базы данных: {error}")
            return False