#консольный интерфейс
from enigma import derive_master_key, split_keys, encrypt_master_key_with_pin, decrypt_master_key_with_pin, encrypt_vault_item, decrypt_vault_item
from postgres import insert_table, show_table
import os
import json

if __name__ == "__main__":

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