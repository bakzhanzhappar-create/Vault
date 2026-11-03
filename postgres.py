import os
import psycopg
from psycopg.types.json import Jsonb
from dotenv import load_dotenv
from uuid import UUID

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

    def create_vault(self) -> bool:
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
        print("Таблица `Vault` успешно создана/проверена!")
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

    def import_db(self, vault_db: dict) -> bool:
        self.create_vault()
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""DELETE FROM vault;""")

                    for entry in vault_db["entries"]:
                        cursor.execute(
                            """INSERT INTO vault(session_id, title, secret) VALUES (%s, %s, %s);""",
                            (entry["session_id"], Jsonb(entry["title"]), Jsonb(entry["secret"])),
                        )
                    conn.commit()
            print("SUCCESSFULLY IMPORTED!")
            return True
        except Exception as error:
            print(f"Ошибка при записи в базу данных во время восстановления: {error}")
            return False