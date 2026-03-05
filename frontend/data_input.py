import yfinance as yf
from yahooquery import Ticker
from datetime import datetime
import psycopg2


# DATABASE CONNECTION


def get_connection():
    return psycopg2.connect(
        host="localhost",
        port="5433",
        database="stock_db",
        user="postgres",
        password="admin"
    )

conn = get_connection()
cursor = conn.cursor()



# COMPANY LIST


tickers = [
    "INFY.NS",
    "ITC.NS"
]



# FETCH DATA


for ticker in tickers:

    stock = yf.Ticker(ticker)
    info = stock.info

    symbol = ticker
    company_name = info.get("longName")
    sector = info.get("sector", "Unknown")
    pe = info.get("trailingPE")
    peg = info.get("pegRatio")
    debt_free_cash = info.get("freeCashflow")
    if debt_free_cash is None:
        debt_free_cash = 0

    # fallback values
    if not company_name:
        company_name = ticker

    if not sector:
        sector = "Unknown"


    
    # PROMOTER HOLDING
    

    promoter_holding = None

    try:
        yq = Ticker(ticker)
        summary = yq.key_stats[ticker]

        promoter_holding = summary.get("heldPercentInsiders")

        if promoter_holding:
            promoter_holding = promoter_holding * 100

    except:
        promoter_holding = None


    
    # INSERT SYMBOL
    

    cursor.execute(
        """
        INSERT INTO symbol(company_symbol, company_name, sector)
        VALUES (%s, %s, %s)
        ON CONFLICT (company_symbol) DO NOTHING
        """,
        (symbol, company_name, sector)
    )


    
    # FETCH SYMBOL ID
    

    cursor.execute(
        "SELECT symbol_id FROM symbol WHERE company_symbol=%s",
        (symbol,)
    )

    company_id = cursor.fetchone()[0]





    financials = stock.quarterly_financials

    latest_ebitda = None
    latest_revenue = None
    latest_net_profit = None

    if not financials.empty:

        for i, col in enumerate(financials.columns[:4]):

            revenue_q = financials.loc["Total Revenue"][col] if "Total Revenue" in financials.index else None
            ebitda_q = financials.loc["EBITDA"][col] if "EBITDA" in financials.index else None
            net_profit_q = financials.loc["Net Income"][col] if "Net Income" in financials.index else None

        # save latest snapshot
            if i == 0:
                latest_ebitda = ebitda_q
                latest_revenue = revenue_q
                latest_net_profit = net_profit_q

            cursor.execute(
            """
            INSERT INTO historical_metrics
            (symbol_id, financial_year, quarter, revenue, ebitda, net_profit, reported_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
                (
                company_id,
                col.year,
                (col.month - 1)//3 + 1,
                revenue_q,
                ebitda_q,
                net_profit_q,
                col.date()
                )
            )


    
    # INSERT FUNDAMENTALS SNAPSHOT
    

    cursor.execute(
    """
    INSERT INTO fundamentals
    (symbol_id, pe, peg, promoter_holding, ebitda, debt_free_cash)
    VALUES (%s, %s, %s, %s, %s, %s)
    """,
    (
    company_id,
    pe,
    peg,
    promoter_holding,
    latest_ebitda,
    debt_free_cash
    )
    )

conn.commit()

print("Data inserted successfully")

conn.close()