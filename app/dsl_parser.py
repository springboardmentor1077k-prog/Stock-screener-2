# app/dsl_parser.py

def parse_filters(query: str):

    filters = []

    query = query.lower()

    if "pe" in query and "less than" in query:
        try:
            value = int(query.split("less than")[-1].split()[0])
            filters.append({
                "field": "pe_ratio",
                "operator": "<",
                "value": value
            })
        except:
            pass

    return filters