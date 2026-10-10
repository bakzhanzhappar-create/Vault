from postgres import create_test_table, insert_table, show_table

def write_table():
    """Тестовая запись в таблицу"""
    title_name = str(input("title name: "))
    secret_text = str(input("secret text: "))
    insert_table(title_name, secret_text)
    return True

while True:
    print("===== TESTING =====")
    ask=str(input("w to write, e, to exit, s to show, c to create "))
    if ask == "w":
        write_table()
    if ask == "s":
        show_table()
        print("1")
    if ask == "c":
        create_test_table()
    if ask == "e":
        break