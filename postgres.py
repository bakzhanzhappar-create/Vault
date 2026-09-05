import psycopg
#Создать отдельный бд, отдельного юзера, продумать структуру адреса, продумать таблицы или условно хорошо все это затестить
conn = psycopg.connect(
    host="localhost",
    port="5432",
    dbname="baga",
    user="postgres",
    password="*password*",
)

cursor = conn.cursor()

cursor.close()
conn.close()