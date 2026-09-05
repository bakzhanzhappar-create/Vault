import psycopg
#продумать структуру адреса, продумать таблицы или условно хорошо все это затестить
conn = psycopg.connect(
    host="localhost",
    port="5432",
    dbname="vault_db",
    user="vault_app",
    password="2006Bakzhan",
)

cursor = conn.cursor()

cursor.close()
conn.close()