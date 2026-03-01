# app/llm.py

def nl_to_dsl(nl_query: str) -> dict:
    """
    Mock LLM for development.
    Converts some basic natural language patterns into DSL.
    """

    query = nl_query.lower()

    dsl = {
        "filters": [],
        "sort_by": "market_cap",
        "order": "desc",
        "limit": 10
    }

    # PE ratio filter
    if "pe" in query and "less than" in query:
        value = int(query.split("less than")[-1].split()[0])
        dsl["filters"].append({
            "field": "pe_ratio",
            "operator": "<",
            "value": value
        })

    # limit
    if "limit" in query:
        try:
            value = int(query.split("limit")[-1].split()[0])
            dsl["limit"] = value
        except:
            pass

    # order
    if "ascending" in query or "asc" in query:
        dsl["order"] = "asc"

    if "descending" in query or "desc" in query:
        dsl["order"] = "desc"

    return dsl