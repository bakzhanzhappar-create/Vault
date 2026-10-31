import json

#норм, можно переписать
def export_vault():
    """Экспорт хранилища в файл .vault"""
    if not CURRENT_DEK:
        print("Сессия не активна!")
        return False

    if not os.path.exists(CONFIG_FILE):
        print("Ошибка: Конфигурация хранилища не найдена.")
        return False

    # Читаем конфигурацию (соль, nonce, зашифрованный DEK)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    # Получаем все зашифрованные записи из базы данных
    rows = show_table()
    entries_list = []
    for session_id, title_json, secret_json in rows:
        entries_list.append({
            "session_id": str(session_id),
            "title": title_json,
            "secret": secret_json
        })

    vault_backup = {
        "version": 1,
        "config": config_data,
        "entries": entries_list
    }

    file_name = input("Введите имя файла для бэкапа (например, my_vault.vault): ").strip()
    if not file_name.endswith(".vault"):
        file_name += ".vault"

    try:
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(vault_backup, f, ensure_ascii=False, indent=4)
        print(f"Резервная копия успешно сохранена в файл: {file_name}")
        return True
    except Exception as e:
        print(f"Ошибка при записи файла: {e}")
        return False

#фигня, надо пересмотреть
def import_vault():
    """Восстановление хранилища из файла .vault с предварительной проверкой"""
    file_name = input("Введите путь к файлу резервной копии (.vault): ").strip()

    if not os.path.exists(file_name):
        print("Ошибка: Файл не найден!")
        return False

    # 1. Проверка структуры файла и JSON
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            vault_backup = json.load(f)
    except Exception as e:
        print(f"Ошибка: Файл поврежден или имеет неверный формат JSON: {e}")
        return False

    if "version" not in vault_backup or "config" not in vault_backup or "entries" not in vault_backup:
        print("Ошибка: Неверная структура файла резервной копии .vault")
        return False

    # 2. Проверка мастер-пароля (пробуем расшифровать DEK из файла)
    pwd = input("Введите мастер-пароль от этой резервной копии для проверки: ")
    #здесь свяжи функцией которая дешифровку делает отдельно для этого. enigma
    try:
        from enigma import derive_kek, decrypt_dek
        import base64

        cfg = vault_backup["config"]
        salt = base64.b64decode(cfg["salt"])
        nonce = base64.b64decode(cfg["nonce"])
        encrypted_dek = base64.b64decode(cfg["encrypted_dek"])

        temp_kek = derive_kek(pwd, salt)
        temp_dek = decrypt_dek(temp_kek, nonce, encrypted_dek)  # Если пароль неверный, здесь упадет ошибка
        print("Пароль верный, структура файла подтверждена.")
    except Exception:
        print("Ошибка: Неверный мастер-пароль или повреждены криптографические данные в файле! Изменения не применены.")
        return False

    # 3. Применение изменений (замена конфига и записей в БД)
    confirm = input("Внимание! Это перезапишет текущее локальное хранилище. Продолжить? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Импорт отменен.")
        return False

    # Перезаписываем конфиг
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(vault_backup["config"], f)

    # Обновляем глобальный ключ сессии на новый
    global CURRENT_DEK
    CURRENT_DEK = temp_dek

    # Очищаем старую таблицу и заливаем данные из бэкапа
#здесь также, но для постгреса.
    from postgres import get_connection, create_test_table
    create_test_table()  # Убедимся, что таблица есть

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Очищаем таблицу перед восстановлением
                cursor.execute("DELETE FROM test_table;")

                # Вставляем записи из бэкапа
                for entry in vault_backup["entries"]:
                    cursor.execute(
                        "INSERT INTO test_table(session_id, title, secret) VALUES (%s, %s, %s);",
                        (entry["session_id"], json.dumps(entry["title"]), json.dumps(entry["secret"]))
                    )
                conn.commit()
        print("Хранилище успешно восстановлено из резервной копии!")
        return True
    except Exception as e:
        print(f"Ошибка при записи в базу данных во время восстановления: {e}")
        return False