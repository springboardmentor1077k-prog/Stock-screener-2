def paginate_query(sql_query, page, page_size):

    offset = (page - 1) * page_size

    sql_query += f" LIMIT {page_size} OFFSET {offset}"

    return sql_query