from database import execute_query


def create_api_response(data):

    response = {
        "status": "success",
        "count": len(data),
        "data": data
    }

    return response


def run_query(sql_query):

    rows = execute_query(sql_query)

    result = create_api_response(rows)

    return result