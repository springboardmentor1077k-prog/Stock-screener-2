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
    "HINDUNILVR.NS",   # FMCG
    "ICICIBANK.NS",    # Banking
    "SBIN.NS",         # Banking
    "LT.NS",           # Infrastructure
    "AXISBANK.NS",     # Banking
    "KOTAKBANK.NS",    # Banking
    "BAJFINANCE.NS",   # NBFC
    "ASIANPAINT.NS",   # Paints
    "MARUTI.NS",       # Automobile
    "TITAN.NS",        # Jewellery
    "ULTRACEMCO.NS",   # Cement
    "SUNPHARMA.NS",    # Pharma
    "WIPRO.NS",        # IT
    "TECHM.NS",        # IT
    "NTPC.NS",         # Power
    "POWERGRID.NS",    # Power
    "ONGC.NS",         # Oil & Gas
    "COALINDIA.NS",    # Mining
    "ADANIENT.NS",     # Conglomerate
    "ADANIPORTS.NS"    # Ports
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
    growth = info.get("earningsGrowth")
    
    
    #PEG + GROWTH
    
    if pe and growth and growth > 0:
        growth_p = growth * 100
        peg = pe / growth_p if growth_p != 0 else 0
    else:
        peg = 0
        
    
    
    
    debt_free_cash = info.get("freeCashflow")
    if debt_free_cash is None:
        debt_free_cash = 0
        


    # fallback values
    if not company_name:
        company_name = ticker

    if not sector:
        sector = "Unknown"


    
    # PROMOTER HOLDING
    promoter_holding = 0

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

    # latest_ebitda = None
    # latest_revenue = None
    # latest_net_profit = None

    # if not financials.empty:

    #     for i, col in enumerate(financials.columns[:4]):

    #         revenue_q = financials.loc["Total Revenue"][col] if "Total Revenue" in financials.index else None
    #         ebitda_q = financials.loc["EBITDA"][col] if "EBITDA" in financials.index else None
    #         net_profit_q = financials.loc["Net Income"][col] if "Net Income" in financials.index else None

    #     # save latest snapshot
    #         if i == 0:
    #             latest_ebitda = ebitda_q
    #             latest_revenue = revenue_q
    #             latest_net_profit = net_profit_q

    #         cursor.execute(
    #         """
    #         INSERT INTO historical_metrics
    #         (symbol_id, financial_year, quarter, revenue, ebitda, net_profit, reported_date)
    #         VALUES (%s,%s,%s,%s,%s,%s,%s)
    #         """,
    #             (
    #             company_id,
    #             col.year,
    #             (col.month - 1)//3 + 1,
    #             revenue_q,
    #             ebitda_q,
    #             net_profit_q,
    #             col.date()
    #             )
    #         )
    
    latest_ebitda = 0
    latest_revenue = 0
    latest_net_profit = 0

    if not financials.empty:

        for i, col in enumerate(financials.columns[:4]):

            revenue_q = financials.loc["Total Revenue"][col] if "Total Revenue" in financials.index else None
            ebitda_q = financials.loc["EBITDA"][col] if "EBITDA" in financials.index else None
            operating_income_q = financials.loc["Operating Income"][col] if "Operating Income" in financials.index else None
            net_profit_q = financials.loc["Net Income"][col] if "Net Income" in financials.index else None

        # FALLBACK LOGIC
            if ebitda_q is not None:
                final_ebitda = ebitda_q
            elif operating_income_q is not None:
                final_ebitda = operating_income_q
            elif net_profit_q is not None:
                final_ebitda = net_profit_q
            else:
                final_ebitda = 0

            revenue_q = revenue_q if revenue_q is not None else 0
            net_profit_q = net_profit_q if net_profit_q is not None else 0

        # save latest snapshot
            if i == 0:
                latest_ebitda = final_ebitda
                latest_revenue = revenue_q
                latest_net_profit = net_profit_q

                cursor.execute(
            """
            INSERT INTO historical_metrics
            (symbol_id, financial_year, quarter, revenue, ebitda, net_profit, reported_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s)

            ON CONFLICT (symbol_id, financial_year, quarter)
            DO UPDATE SET
            revenue = EXCLUDED.revenue,
            ebitda = EXCLUDED.ebitda,
            net_profit = EXCLUDED.net_profit,
            reported_date = EXCLUDED.reported_date
            """,
            (
            company_id,
            col.year,
            (col.month - 1)//3 + 1,
            revenue_q,
            final_ebitda,
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

    ON CONFLICT (symbol_id)
    DO UPDATE SET
    pe = EXCLUDED.pe,
    peg = EXCLUDED.peg,
    promoter_holding = EXCLUDED.promoter_holding,
    ebitda = EXCLUDED.ebitda,
    debt_free_cash = EXCLUDED.debt_free_cash
    """,
    (   
    company_id,
    pe or 0,
    peg or 0,
    promoter_holding or 0,
    latest_ebitda or 0,
    debt_free_cash or 0
    )
    )
conn.commit()

print("Data inserted successfully")

conn.close()