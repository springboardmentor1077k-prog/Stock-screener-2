import psycopg2


def execute_query(sql, values):

    con = psycopg2.connect(
        host="localhost",
        port="5433",
        database="stock_db",
        user="postgres",
        password="admin"
    )
    cursor = con.cursor()


    cursor.execute(sql,values)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    # convert rows → dictionary
    results = []

    for row in rows:
        results.append(dict(zip(columns, row)))

    cursor.close()
    con.close()

    return results

