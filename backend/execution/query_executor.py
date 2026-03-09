from sqlalchemy import text
from database import engine


def execute_query(sql_query: str, params: list):

    try:
        with engine.connect() as conn:

            result = conn.execute(text(sql_query), params)

            rows = result.fetchall()

            columns = result.keys()

    except Exception:

        return {
            "error": {
                "code": "DB_EXECUTION_ERROR",
                "message": "Database execution failed"
            }
        }

    # Convert rows to dictionaries
    results = []

    for row in rows:
        record = dict(zip(columns, row))
        results.append(record)

    # Handle empty results
    if len(results) == 0:

        return {
            "meta": {
                "count": 0
            },
            "data": [],
            "message": "No companies satisfy the condition"
        }

    # Success response
    return {
        "meta": {
            "count": len(results)
        },
        "data": results
        }