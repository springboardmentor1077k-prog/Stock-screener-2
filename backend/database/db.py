import aiosqlite
import os

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "stock_screener.db"
)

async def execute_query(sql, params):

    async with aiosqlite.connect(DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        cursor = await db.execute(sql, params)

        rows = await cursor.fetchall()

        return [dict(row) for row in rows]