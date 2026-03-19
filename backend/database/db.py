import aiosqlite
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "stock_screener.db")


async def execute_query(sql, params):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(sql, params)
            rows = await cursor.fetchall()

            return [dict(row) for row in rows]

    except Exception as e:
        print("DB ERROR:", e)
        return []