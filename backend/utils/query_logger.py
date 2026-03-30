import logging
import time

logger = logging.getLogger("query_logger")

def log_query(user_query, sql_query, execution_time=None):
    if execution_time:
        logger.info(
            f"UserQuery: {user_query} | SQL: {sql_query} | Time: {execution_time:.4f}s"
        )
    else:
        logger.info(
            f"UserQuery: {user_query} | SQL: {sql_query}"
        )