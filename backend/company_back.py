from fastapi import APIRouter, HTTPException
from database_back import get_connection

router = APIRouter()

@router.post("/company-details")
def get_company_details(data: dict):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                s.company_name,
                s.company_symbol,
                s.sector,
                d.description,
                d.founded_year,
                d.company_type,
                d.market_cap,
                
                 f.pe,
                f.peg,
                f.promoter_holding,
                f.ebitda,
                f.debt_free_cash

            FROM symbol s
           
        LEFT JOIN company_details d 
        ON s.symbol_id = d.symbol_id

        LEFT JOIN fundamentals f
        ON s.symbol_id = f.symbol_id

        WHERE s.company_symbol = %s
        """, (data["symbol"],))

        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Company not found")

        return {
        "name": row[0],
        "symbol": row[1],
        "sector": row[2],

        "description": row[3],
        "founded": row[4],
        "type": row[5],
        "market_cap": row[6],

    "fundamentals": {
        "pe": row[7],
        "peg": row[8],
        "promoter_holding": row[9],
        "ebitda": row[10],
        "debt_free_cash": row[11]
        }
    }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    