#консольный интерфейс
from enigma import derive_master_key, split_keys, encrypt_master_key_with_pin, decrypt_master_key_with_pin, encrypt_vault_item, decrypt_vault_item
from postgres import insert_table, show_table
import os
import json

while True:
    ask=input("Create secret (create)? Show secret text (show)? End (end)")
    if "create" in ask.lower():
        print("=== START ===")
        password = input("Придумайте Master Password: ")
        pin = input("Придумайте локальный PIN (например, 1234): ")

        # 1. Генерация уникальной соли пользователя (хранится открыто)
        user_salt = os.urandom(16)

        # 2. Получение Master Key и его расщепление
        master_key = derive_master_key(password, user_salt)
        enc_key, auth_key = split_keys(master_key)

        # 3. Шифруем Master Key ПИН-кодом (это уходит в IndexedDB)
        local_pin_vault = encrypt_master_key_with_pin(master_key, pin)

        print("\n[Успешно] Сессия создана!")
        print(f"Auth Key (отправляется на сервер): {auth_key.hex()[:20]}...")
        print(f"Encryption Key (только в RAM):     {enc_key.hex()[:20]}...")


        print("\n=== ШИФРОВАНИЕ ЗАПИСИ ===")
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



    if "show" in ask.lower():
        print("Showing from db")
        entered_pin = input("\nВведите PIN для быстрого входа: ")
        key = input("\n put master key")
        user_salt = b"979954d61f152338cc042f990b6c3a92"
        pin = input("\n from db show pin")
        try:
            master_key = derive_master_key(key, user_salt)
            enc_key, auth_key = split_keys(master_key)

        # 3. Шифруем Master Key ПИН-кодом (это уходит в IndexedDB)
            local_pin_vault = encrypt_master_key_with_pin(master_key, pin)
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

        except Exception as error:
            print(f"\n[Ошибка] Неверный PIN-код или ошибка расшифровки! ({error})")
    if "end" in ask.lower():
        print("=== END ===")
        break
#show сценарии пока не готов