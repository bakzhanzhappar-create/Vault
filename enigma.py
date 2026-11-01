import base64
import json
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

CONFIG_FILE = "vault_config.json"


def generate_salt() -> bytes:
    return os.urandom(16)


def derive_kek(master_password: str, salt: bytes) -> bytes | None:
    try:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600_000,
        )
        return kdf.derive(master_password.encode("utf-8"))
    except Exception as error:
        print(f"{error}")
        return None

def generate_dek() -> bytes:
    return os.urandom(32)


def encrypt_dek(kek: bytes, dek: bytes) -> tuple[bytes, bytes] | None:
    try:
        aesgcm = AESGCM(kek)
        nonce = os.urandom(12)
        encrypted_dek = aesgcm.encrypt(nonce, dek, None)
        return nonce, encrypted_dek
    except Exception as error:
        print(f"{error}")
        return None

def decrypt_dek(kek: bytes, nonce: bytes, encrypted_dek: bytes) -> bytes | None:
    try:
        aesgcm = AESGCM(kek)
        return aesgcm.decrypt(nonce, encrypted_dek, None)
    except ValueError as error:
        print(f"ERROR {error}")
        return None


def encrypt_vault_item(dek: bytes, item_id: str, data: dict) -> dict | None:
    """Шифрование словаря данных с привязкой ID в качестве AAD."""
    try:
        aesgcm = AESGCM(dek)
        nonce = os.urandom(12)
        plaintext_bytes = json.dumps(data).encode("utf-8")
        aad = item_id.encode("utf-8")
        ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, aad)

        return {
            "nonce": base64.b64encode(nonce).decode("utf-8"),
            "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
        }
    except Exception as error:
        print(f"{error}")
        return None


def decrypt_vault_item(dek: bytes, item_id: str, encrypted_item: dict) -> dict | None:
    """Расшифровка зашифрованного словаря данных."""
    try:
        aesgcm = AESGCM(dek)
        nonce = base64.b64decode(encrypted_item["nonce"])
        ciphertext = base64.b64decode(encrypted_item["ciphertext"])
        aad = item_id.encode("utf-8")

        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, aad)
        return json.loads(plaintext_bytes.decode("utf-8"))
    except Exception as error:
        print(f"{error}")
        return None


def initialize_vault(master_password: str) -> bool:
    try:
        salt = generate_salt()
        kek = derive_kek(master_password, salt)
        dek = generate_dek()
        nonce, encrypted_dek = encrypt_dek(kek, dek)

        config = {
            "salt": base64.b64encode(salt).decode("utf-8"),
            "nonce": base64.b64encode(nonce).decode("utf-8"),
            "encrypted_dek": base64.b64encode(encrypted_dek).decode("utf-8"),
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f)
        return True
    except Exception as error:
        print(f"{error}")
        return False

def load_dek(master_password: str) -> bytes | None:
    try:
        if not os.path.exists(CONFIG_FILE):
            raise FileNotFoundError("config wasnt initialized.")

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)

        salt = base64.b64decode(config["salt"])
        nonce = base64.b64decode(config["nonce"])
        encrypted_dek = base64.b64decode(config["encrypted_dek"])

        kek = derive_kek(master_password, salt)
        return decrypt_dek(kek, nonce, encrypted_dek)
    except Exception as error:
        print(f"{error}")
        return None


def import_password(password: str, vault_backup: dict )-> bytes | None:
    try:
        cfg = vault_backup["config"]
        salt = base64.b64decode(cfg["salt"])
        nonce = base64.b64decode(cfg["nonce"])
        encrypted_dek = base64.b64decode(cfg["encrypted_dek"])

        temp_kek = derive_kek(password, salt)
        temp_dek = decrypt_dek(temp_kek, nonce, encrypted_dek)
        print("Пароль верный, структура файла подтверждена.")
        return temp_dek
    except Exception as error:
        print(f"Ошибка: Неверный мастер-пароль или повреждены криптографические данные в файле! Изменения не применены. {error}")
        return None