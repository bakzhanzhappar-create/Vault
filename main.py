import os
import uuid
from postgres import (
    create_test_table, insert_table, show_table,
    get_secret_by_id, update_by_id, delete_by_id, check_uuid
)
from enigma import initialize_vault, load_dek, encrypt_vault_item, decrypt_vault_item, CONFIG_FILE

CURRENT_DEK = None

create_test_table()


def export_vault():
    if not CURRENT_DEK:
        print("Сессия не активна!")
        return False

    if not os.path.exists(CONFIG_FILE):
        print("Ошибка конфигурации файл не найдено")



def authenticate_session():
    global CURRENT_DEK
    print("===== АВТОРИЗАЦИЯ / ИНИЦИАЛИЗАЦИЯ ХРАНИЛИЩА =====")
    if not os.path.exists(CONFIG_FILE):
        print("Конфигурация не найдена. Создадим новый мастер-пароль.")
        while True:
            pwd = input("Введите новый мастер-пароль: ")
            if pwd.strip():
                initialize_vault(pwd)
                print("Мастер-пароль успешно создан!")
                break
            print("Пароль не может быть пустым.")

    while True:
        pwd = input("Введите мастер-пароль для разблокировки сессии: ")
        try:
            CURRENT_DEK = load_dek(pwd)
            print("Сессия успешно разблокирована!\n")
            break
        except Exception:
            print("Неверный пароль! Попробуйте снова.")


def write_table():
    if not CURRENT_DEK:
        print("Сессия не активна!")
        return False

    title_name = str(input("title name: "))
    secret_text = str(input("secret text: "))

    # Генерируем UUID заранее — он идет и в БД, и как AAD для криптографии
    session_id = uuid.uuid4()

    payload = {
        "title": title_name,
        "secret": secret_text
    }

    # Шифруем с привязкой к session_id (AAD)
    encrypted_payload = encrypt_vault_item(CURRENT_DEK, str(session_id), payload)

    dict_to_insert = {
        "title": {"name": title_name},
        "secret": encrypted_payload
    }

    insert_table(session_id, dict_to_insert)
    print(f"Запись успешно зашифрована и сохранена. ID: {session_id}")
    return True


def show_secret():
    """Поиск по ID с полной расшифровкой"""
    if not CURRENT_DEK:
        print("Сессия не активна!")
        return False

    raw_uuid = input("uuid code: ").strip()
    checked_uuid = check_uuid(raw_uuid)
    if checked_uuid is None:
        return False

    result = get_secret_by_id(checked_uuid)
    if result is None or result is False:
        print("Запись не найдена!")
        return False

    title_json, secret_json = result
    try:
        # Расшифровываем, передавая тот же UUID в качестве AAD
        decrypted_data = decrypt_vault_item(CURRENT_DEK, str(checked_uuid), secret_json)
        print(f"\n[РАСШИФРОВАНО УСПЕШНО]")
        print(f"ID: {checked_uuid}")
        print(f"Title: {decrypted_data['title']}")
        print(f"Secret: {decrypted_data['secret']}\n")
        return True
    except Exception as e:
        print(f"Ошибка расшифровки записи (возможно повреждены данные или нарушен AAD): {e}")
        return False


def list_entries():
    """Вывод сырого шифротекста для всех записей (команда s)"""
    if not CURRENT_DEK:
        print("Сессия не активна!")
        return

    rows = show_table()
    if not rows:
        print("Хранилище пусто.")
        return

    print("\n===== СПИСОК ЗАПИСЕЙ (RAW CIPHERTEXT) =====")
    for session_id, title_json, secret_json in rows:
        print(f"ID: {session_id}")
        print(f"  Title JSON: {title_json}")
        print(f"  Encrypted Secret: {secret_json}\n")


def secret_update():
    if not CURRENT_DEK:
        print("Сессия не активна!")
        return False

    checked_uuid = check_uuid(input("uuid code: ").strip())
    if checked_uuid is None:
        return False

    new_title = str(input("new title: "))
    new_secret = str(input("new secret: "))

    payload = {
        "title": new_title,
        "secret": new_secret
    }

    encrypted_payload = encrypt_vault_item(CURRENT_DEK, str(checked_uuid), payload)

    dict_to_update = {
        "title": {"name": new_title},
        "secret": encrypted_payload
    }

    changed = update_by_id(checked_uuid, dict_to_update)
    print("changed" if changed else "Запись не найдена")
    return changed


def delete_secret():
    checked_uuid = check_uuid(input("uuid code: ").strip())
    if checked_uuid is None:
        return False

    deleted = delete_by_id(checked_uuid)
    print("deleted" if deleted else "Запись не найдена")
    return deleted


if __name__ == "__main__":
    authenticate_session()

    while True:
        print("\n===== TESTING MENU =====")
        ask = str(input(
            "w to write, e to exit, s to show all, c to create table, id to show by id, u to update, d to delete: ")).strip()
        if ask == "w":
            write_table()
        elif ask == "s":
            list_entries()
        elif ask == "c":
            create_test_table()
        elif ask == "id":
            show_secret()
        elif ask == "u":
            secret_update()
        elif ask == "d":
            delete_secret()
        elif ask == "e":
            print("Выход из программы.")
            break