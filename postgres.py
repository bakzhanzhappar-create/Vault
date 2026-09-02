import psycopg

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