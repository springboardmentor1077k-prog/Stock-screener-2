import re
from dsl_schema import QueryDSL, Condition


def parse_query(user_query: str):
    user_query = user_query.lower()

    # ✅ Convert natural language → symbols
    user_query = user_query.replace("less than", "<")
    user_query = user_query.replace("greater than", ">")
    user_query = user_query.replace("below", "<")
    user_query = user_query.replace("above", ">")

    conditions = []

    # -------- PE Ratio --------
    pe_match = re.search(r"(pe|pe_ratio)\s*(<|>|<=|>=|=)\s*(\d+)", user_query)
    if pe_match:
        operator = pe_match.group(2)
        value = int(pe_match.group(3))
        conditions.append(Condition("pe_ratio", operator, value))

    # -------- Profit --------
    profit_match = re.search(r"(profit|net_profit)\s*(<|>|<=|>=|=)\s*(\d+)", user_query)
    if profit_match:
        operator = profit_match.group(2)
        value = int(profit_match.group(3))
        conditions.append(Condition("net_profit", operator, value))

    # -------- Revenue --------
    revenue_match = re.search(r"revenue\s*(<|>|<=|>=|=)\s*(\d+)", user_query)
    if revenue_match:
        operator = revenue_match.group(1)
        value = int(revenue_match.group(2))
        conditions.append(Condition("revenue", operator, value))

    # -------- SECTOR (IT) --------
    if "it" in user_query:
        conditions.append(Condition("sector", "=", "IT"))

    # ✅ If no valid conditions → return None
    if not conditions:
        return None

    # -------- Build DSL --------
    dsl = QueryDSL(conditions=conditions)

    return dsl