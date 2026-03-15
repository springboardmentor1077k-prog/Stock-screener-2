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


def parse_query(user_query: str):

    query = user_query.lower()

    for field_text, field_db in FIELDS.items():

        if field_text in query:

            for op_text, op_symbol in OPERATORS.items():

                if op_text in query:

                    value = re.findall(r'\d+', query)

                    if value:
                        value = int(value[0])

                        condition = Condition(
                            field=field_db,
                            operator=op_symbol,
                            value=value
                        )

                        return QueryDSL(
                            conditions=[condition],
                            logic="AND"
                        )

    raise ValueError("Unable to parse query")