import base64
import json
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def derive_kek(master_password: str, salt: bytes) -> bytes:
    """Генерация ключа шифрования ключа (KEK) из Мастер-пароля через PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )
    return kdf.derive(master_password.encode())


def generate_dek() -> bytes:
    """Генерация случайного ключа данных (DEK) для шифрования записей."""
    return os.urandom(32)


def encrypt_dek(kek: bytes, dek: bytes) -> tuple[bytes, bytes]:
    """Шифрование DEK с помощью KEK (тот самый 'маленький сейф')."""
    aesgcm = AESGCM(kek)
    nonce = os.urandom(12)
    encrypted_dek = aesgcm.encrypt(nonce, dek, None)
    return nonce, encrypted_dek


def decrypt_dek(kek: bytes, nonce: bytes, encrypted_dek: bytes) -> bytes:
    """Расшифровка DEK с помощью KEK (открытие 'маленького сейфа')."""
    aesgcm = AESGCM(kek)
    return aesgcm.decrypt(nonce, encrypted_dek, None)


def encrypt_vault_item(dek: bytes, item_id: str, data: dict) -> dict:
    """Шифрование одной записи с помощью DEK."""
    aesgcm = AESGCM(dek)
    nonce = os.urandom(12)
    plaintext_bytes = json.dumps(data).encode("utf-8")
    aad = item_id.encode("utf-8")  # ID записи привязывается к шифру (защита от подмены)
    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, aad)

    return {
        "item_id": item_id,
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
    }


def decrypt_vault_item(dek: bytes, encrypted_item: dict) -> dict:
    """Расшифровка одной записи с помощью DEK."""
    aesgcm = AESGCM(dek)
    nonce = base64.b64decode(encrypted_item["nonce"])
    ciphertext = base64.b64decode(encrypted_item["ciphertext"])
    aad = encrypted_item["item_id"].encode("utf-8")

    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, aad)
    return json.loads(plaintext_bytes.decode("utf-8"))