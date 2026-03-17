from app.database.connection import get_connection


class PortfolioService:

    @staticmethod
    def add_stock(user_id: int, company_id: int, quantity: int):
        conn = get_connection()
        cursor = conn.cursor()

        # Check if stock already exists in portfolio
        cursor.execute(
            """
            SELECT quantity FROM portfolio
            WHERE user_id = ? AND company_id = ?
            """,
            (user_id, company_id)
        )

        row = cursor.fetchone()

        if row:
            # Update quantity
            new_qty = row[0] + quantity
            cursor.execute(
                """
                UPDATE portfolio
                SET quantity = ?
                WHERE user_id = ? AND company_id = ?
                """,
                (new_qty, user_id, company_id)
            )
        else:
            # Insert new stock
            cursor.execute(
                """
                INSERT INTO portfolio (user_id, company_id, quantity)
                VALUES (?, ?, ?)
                """,
                (user_id, company_id, quantity)
            )

        conn.commit()
        conn.close()

        return {"message": "Stock added to portfolio"}

    @staticmethod
    def remove_stock(user_id: int, company_id: int):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM portfolio
            WHERE user_id = ? AND company_id = ?
            """,
            (user_id, company_id)
        )

        conn.commit()
        conn.close()

        return {"message": "Stock removed from portfolio"}

    @staticmethod
    def get_portfolio(user_id: int):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                p.company_id,
                s.symbol,
                s.company_name,
                s.sector,
                p.quantity,
                p.added_at
            FROM portfolio p
            JOIN symbols s
            ON p.company_id = s.id
            WHERE p.user_id = ?
            """,
            (user_id,)
        )

        rows = cursor.fetchall()
        conn.close()

        portfolio = []

        for row in rows:
            portfolio.append({
                "company_id": row[0],
                "symbol": row[1],
                "company_name": row[2],
                "sector": row[3],
                "quantity": row[4],
                "added_at": row[5]
            })

        return portfolio