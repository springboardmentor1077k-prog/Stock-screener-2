def parse_dsl(query):

    query = query.replace("GET stocks", "SELECT * FROM stocks")

    return query