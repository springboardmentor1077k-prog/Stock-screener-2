import psycopg2


def get_connection():

    conn = psycopg2.connect(
        host="localhost",
        database="stocks_db",
        user="postgres",
        password="Taekookilu"
    )

    return conn