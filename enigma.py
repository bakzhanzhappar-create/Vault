# Это временный файл где будет реализовано шифрование.
#Необходимо доказать что мы можем Надежно, Доступно и Безопасно хранить данные в бд


# У юзера три ключа.
# Симметричный ключ (AES-GCM 256) шифрует записи. Далее будет шифрован еще раз пинкодом
# Auth Key доказательство знания мастер-пароля без его раскрытия.
# Асимметричная пара ключей (Ed25519 или ECDSA P-256), уникальная для каждого девайса (ПК, телефон, планшет).
import base64
import json
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# =====================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ КРИПТОГРАФИИ
# =====================================================================


def derive_master_key(master_password: str, salt: bytes) -> bytes:
    """Генерация тяжелого Master Key из Master Password через PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )
    return kdf.derive(master_password.encode())


def split_keys(master_key: bytes) -> tuple[bytes, bytes]:
    """Расщепление Master Key на Encryption Key и Auth Key с помощью HKDF."""
    enc_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"vault-data-encryption",
    ).derive(master_key)

    auth_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"server-authentication",
    ).derive(master_key)

    return enc_key, auth_key


def encrypt_master_key_with_pin(master_key: bytes, pin: str) -> dict:
    """Шифрование Master Key коротким ПИН-кодом для локального хранения."""
    pin_salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=pin_salt,
        iterations=100_000,  # Для ПИН-кода меньше итераций для быстрого входа
    )
    pin_derived_key = kdf.derive(pin.encode())

    aesgcm = AESGCM(pin_derived_key)
    nonce = os.urandom(12)
    encrypted_mk = aesgcm.encrypt(nonce, master_key, None)

    return {
        "pin_salt": base64.b64encode(pin_salt).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "encrypted_master_key": base64.b64encode(encrypted_mk).decode(),
    }


def decrypt_master_key_with_pin(pin_vault: dict, pin: str) -> bytes:
    """Расшифровка Master Key с помощью ПИН-кода."""
    pin_salt = base64.b64decode(pin_vault["pin_salt"])
    nonce = base64.b64decode(pin_vault["nonce"])
    encrypted_mk = base64.b64decode(pin_vault["encrypted_master_key"])

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=pin_salt,
        iterations=100_000,
    )
    pin_derived_key = kdf.derive(pin.encode())

    aesgcm = AESGCM(pin_derived_key)
    return aesgcm.decrypt(nonce, encrypted_mk, None)


def encrypt_vault_item(enc_key: bytes, item_id: str, data: dict) -> dict:
    """Шифрование одной записи (логин/пароль/заметка) ключом Encryption Key."""
    aesgcm = AESGCM(enc_key)
    nonce = os.urandom(12)
    plaintext_bytes = json.dumps(data).encode("utf-8")
    aad = item_id.encode("utf-8")  # ID записи привязывается к шифру
    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, aad)
    encypted_nonce = base64.b64encode(nonce).decode()
    encrypted_ciphertext = base64.b64encode(ciphertext).decode()
    return {
        "item_id": item_id,
        "nonce": encypted_nonce,
        "ciphertext": encrypted_ciphertext,
    }


def decrypt_vault_item(enc_key: bytes, encrypted_item: dict) -> dict:
    """Расшифровка записи."""
    aesgcm = AESGCM(enc_key)
    nonce = base64.b64decode(encrypted_item["nonce"])
    ciphertext = base64.b64decode(encrypted_item["ciphertext"])
    aad = encrypted_item["item_id"].encode("utf-8")

    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, aad)
    return json.loads(plaintext_bytes.decode("utf-8"))