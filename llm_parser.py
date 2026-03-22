import re
from dsl_schema import QueryDSL, Condition

FIELDS = {
    "pe ratio": "pe_ratio",
    "sector": "sector",
    "market cap": "market_cap",
    "revenue": "revenue",
    "profit": "profit"
}

OPERATORS = {
    "<": "<",
    ">": ">",
    "=": "=",
    "less than": "<",
    "greater than": ">"
}


#  NEW FUNCTION (Step 9)
def extract_time_filter(query):
    match = re.search(r'last (\d+) quarters', query)
    
    if match:
        return {
            "type": "last_n_quarters",
            "value": int(match.group(1))
        }
    
    return None


def parse_query(user_query: str):
    query = user_query.lower()

    conditions = []
    time_filter = extract_time_filter(query)   #  NEW

    # extract numbers
    numbers = re.findall(r'\d+', query)
    value = int(numbers[0]) if numbers else None

    for field_text, field_db in FIELDS.items():
        if field_text in query:

            for op_text, op_symbol in OPERATORS.items():
                if op_text in query:

                    if value is not None:
                        condition = Condition(
                            field=field_db,
                            operator=op_symbol,
                            value=value
                        )
                        conditions.append(condition)

    #  RETURN DSL WITH TIME FILTER
    return QueryDSL(
        conditions=conditions,
        time_filter=time_filter
    )