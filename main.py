from postgres import create_test_table, insert_table, show_table, get_secret_by_id, update_by_id, delete_by_id, check_uuid


def write_table():
    """Тестовая запись в таблицу"""
    title_name = str(input("title name: "))
    secret_text = str(input("secret text: "))
    dicted_secret={
        "title":title_name,
        "secret":secret_text
    }
    insert_table(dicted_secret)
    return True


def show_secret():
    checked_uuid = check_uuid(input("uuid code: ").strip())

    if checked_uuid is None:
        return False

    result = get_secret_by_id(checked_uuid)

    if result is None:
        print("Запись не найдена!")
        return False

    title, secret = result
    print(f"{title}: {secret}")
    return True


def list_entries():
    for id, title, secret in show_table():
        print(f"{id} [ {title}: {secret} ]")


def secret_update():
    checked_uuid = check_uuid(input("uuid code: ").strip())
    new_title= str(input("new title: "))
    new_secret = str(input("new secret: "))
    dicted_secret={
        "title":new_title,
        "secret":new_secret
    }
    changed = update_by_id(checked_uuid, dicted_secret)
    print("changed" if changed else "Запись не найдена")
    return changed


def delete_secret():
    checked_uuid = check_uuid(input("uuid code: ").strip())  # Тоже добавляем check_uuid

    if checked_uuid is None:
        return False

    deleted = delete_by_id(checked_uuid)
    print("deleted" if deleted else "Запись не найдена")
    return deleted

while True:
    print("===== TESTING =====")
    ask=str(input("w to write, e, to exit, s to show, c to create, id to show by id, u to update secret, d to delete secret "))
    if ask == "w":
        write_table()
    if ask == "s":
        list_entries()
    if ask == "c":
        create_test_table()
    if ask == "id":
        show_secret()
    if ask == "u":
        secret_update()
    if ask == "d":
        delete_secret()
    if ask == "e":
        break