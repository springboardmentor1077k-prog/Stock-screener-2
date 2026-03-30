import aiosqlite
import os
import time
import logging

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")

logger = logging.getLogger("query_logger")

async def execute_query(sql, params):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            start_time = time.time()

            cursor = await db.execute(sql, params)
            rows = await cursor.fetchall()

            end_time = time.time()
            execution_time = end_time - start_time

            logger.info(f"Execution Time: {execution_time:.4f}s | SQL: {sql}")

            return [dict(row) for row in rows], execution_time
    
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return [], 0