import logging

logger = logging.getLogger("query_logger")

def log_query(user_query, sql_query):

    logger.info(
        f"UserQuery: {user_query} | SQL: {sql_query}"
    )