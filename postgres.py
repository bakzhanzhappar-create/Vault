import os
import psycopg
import subprocess
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

#все равно надо чекать. багованный
    def backup(self, backup_dir: str = ".") -> str | None:
        """
        Создает резервную копию базы данных в виде SQL-скрипта.
        Возвращает путь к созданному файлу или None в случае ошибки.
        """
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        dbname = os.getenv("DB_NAME", "vault_db")
        user = os.getenv("DB_USER", "vault_app")
        password = os.getenv("DB_PASSWORD", "")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"backup_{dbname}_{timestamp}.sql")

        # Кроссплатформенный вызов: на Linux/Docker ищет в PATH,
        # на Windows можно при желании переопределить через переменные окружения
        pg_dump_path = os.getenv("PG_DUMP_PATH", "pg_dump")

        cmd = [
            pg_dump_path,
            "-h", host,
            "-p", str(port),
            "-U", user,
            "-F", "p",
            "-f", backup_file,
            dbname
        ]

        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password

        try:
            subprocess.run(
                cmd,
                env=env,
                check=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True
            )
            print(f"Бэкап успешно создан: {backup_file}")
            return backup_file
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при создании бэкапа: {e.stderr}")
            return None
        except FileNotFoundError:
            print("Ошибка: утилита pg_dump не найдена. Убедитесь, что PostgreSQL клиент установлен и доступен в PATH.")
            return None

    # все равно надо чекать. багованный
    def restore(self, backup_file: str) -> bool | None:
        """
        Восстанавливает базу данных из текстового SQL-файла с помощью psql.
        """
        if not os.path.exists(backup_file):
            print(f"Файл бэкапа не найден: {backup_file}")
            return False

        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        dbname = os.getenv("DB_NAME", "vault_db")
        user = os.getenv("DB_USER", "vault_app")
        password = os.getenv("DB_PASSWORD", "")

        psql_path = os.getenv("PSQL_PATH", "psql")

        cmd = [
            psql_path,
            "-h", host,
            "-p", str(port),
            "-U", user,
            "-d", dbname,
            "-f", backup_file
        ]

        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password

        try:
            subprocess.run(
                cmd,
                env=env,
                check=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True
            )
            print(f"База данных успешно восстановлена из файла: {backup_file}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при восстановлении базы данных: {e.stderr}")
            return False
        except FileNotFoundError:
            print("Ошибка: утилита psql не найдена.")
            return None