from postgres import create_test_table, insert_table, show_table, get_secret_by_id

def write_table():
    """Тестовая запись в таблицу"""
    title_name = str(input("title name: "))
    secret_text = str(input("secret text: "))
    insert_table(title_name, secret_text)
    return True


def by_id():
    session_id = str(input("session id: "))
    print(get_secret_by_id(session_id))
    return True


def list_entries():
    for id, title, secret in show_table():
        print(f"{id} [ {title}: {secret} ]")


while True:
    print("===== TESTING =====")
    ask=str(input("w to write, e, to exit, s to show, c to create, id to show by id "))
    if ask == "w":
        write_table()
    if ask == "s":
        list_entries()
    if ask == "c":
        create_test_table()
    if ask == "id":
        by_id()
    if ask == "e":
        break