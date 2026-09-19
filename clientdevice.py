# Это временный файл где будет имитироваться связь клиента и сервера
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

from postgres import create_test_table, insert_table, show_table

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


# =====================================================================
# КОНСОЛЬНЫЙ СЦЕНАРИЙ ИСПОЛЬЗОВАНИЯ
# =====================================================================

if __name__ == "__main__":
    # Инициализируем таблицу в БД при запуске
    create_test_table()

    print("=== 1. РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ ===")
    password = input("Придумайте Master Password: ")
    pin = input("Придумайте локальный PIN (например, 1234): ")

    # 1. Генерация уникальной соли пользователя (хранится открыто)
    user_salt = os.urandom(16)

    # 2. Получение Master Key и его расщепление
    master_key = derive_master_key(password, user_salt)
    enc_key, auth_key = split_keys(master_key)

    # 3. Шифруем Master Key ПИН-кодом (это уходит в IndexedDB)
    local_pin_vault = encrypt_master_key_with_pin(master_key, pin)

    print("\n[Успешно] Аккаунт создан!")
    print(f"Auth Key (отправляется на сервер): {auth_key.hex()[:20]}...")
    print(f"Encryption Key (только в RAM):     {enc_key.hex()[:20]}...")

    print("\n=== 2. ШИФРОВАНИЕ ЗАПИСИ (CLIENT-SIDE) ===")
    title_name = str(input("Title: "))
    text = str(input("Text: "))
    secret_note = {
        "title": f"{title_name}",
        "text": f"{text}",
        "user_id": f"{user_salt.hex()}",
    }

    # Шифруем данные
    item_payload = encrypt_vault_item(enc_key, "item-uuid-001", secret_note)

    # Запись зашифрованных данных в БД PostgreSQL
    # В таблицу с JSON-полями передаем строковые представления JSON
    db_title = json.dumps({"title": title_name})
    db_secret = json.dumps(item_payload)
    db_user_id = json.dumps({"user_id": user_salt.hex()})

    insert_table(db_title, db_secret, db_user_id)
    print("\n[БД] Запись успешно сохранена в PostgreSQL!")

    print("\n=== 3. ЭМУЛЯЦИЯ ПЕРЕЗАПУСКА ПРИЛОЖЕНИЯ ===")
    # Очищаем оперативку от ключей
    del master_key, enc_key, auth_key

    print("Приложение закрыто. Ключи из RAM удалены.")
    entered_pin = input("\nВведите PIN для быстрого входа: ")

    try:
        # Восстанавливаем Master Key по ПИН-коду из IndexedDB
        restored_mk = decrypt_master_key_with_pin(local_pin_vault, entered_pin)
        restored_enc_key, _ = split_keys(restored_mk)

        print("\n[Успех] PIN верный! Master Key восстановлен.")

        # Чтение сохраненной записи из БД
        print("\n[БД] Текущее содержимое таблицы:")
        show_table()

        # Расшифровываем payload
        decrypted_secret = decrypt_vault_item(restored_enc_key, item_payload)

        print("\nРасшифрованные данные из хранилища:")
        print(json.dumps(decrypted_secret, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"\n[Ошибка] Неверный PIN-код или ошибка расшифровки! ({e})")
#организовать код
#чтобы приготовить к тестовой вебке