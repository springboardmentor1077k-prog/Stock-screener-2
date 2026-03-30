# app/llm.py

from app.dsl_parser import parse_filters
import re


def nl_to_dsl(query: str):
    text = query.lower()

    # 🔥 DEFAULT DSL STRUCTURE
    dsl = {
        "filters": [],
        "sort_by": "pe_ratio",
        "order": "asc",
        "limit": 10
    }

    # 🧠 STEP 1: BASE FILTERS (from parser)
    dsl["filters"] = parse_filters(query)

    # 🧠 STEP 2: INTENT-BASED FILTERS

    # cheap / undervalued
    if "cheap" in text or "undervalued" in text:
        dsl["filters"].append({
            "field": "pe_ratio",
            "operator": "<",
            "value": 30
        })

    # very cheap
    if "very cheap" in text:
        dsl["filters"].append({
            "field": "pe_ratio",
            "operator": "<",
            "value": 10
        })

    # expensive
    if "expensive" in text:
        dsl["filters"].append({
            "field": "pe_ratio",
            "operator": ">",
            "value": 30
        })

    # growth
    if "growth" in text:
        dsl["filters"].append({
            "field": "pe_ratio",
            "operator": "<",
            "value": 25
        })

    # 🧠 STEP 3: DIRECT PATTERN (pe < 20)
    match = re.search(r'pe\s*(<|>)\s*(\d+)', text)

    if match:
        op = match.group(1)
        val = int(match.group(2))

        dsl["filters"].append({
            "field": "pe_ratio",
            "operator": op,
            "value": val
        })

    # 🧠 STEP 4: LIMIT
    limit_match = re.search(r'limit\s*(\d+)', text)
    if limit_match:
        dsl["limit"] = int(limit_match.group(1))

    # 🧠 STEP 5: SORTING
    if "descending" in text or "highest" in text:
        dsl["order"] = "desc"

    if "ascending" in text or "lowest" in text:
        dsl["order"] = "asc"

    # 🧠 STEP 6: REMOVE DUPLICATE FILTERS
    unique_filters = []
    seen = set()

    for f in dsl["filters"]:
        key = (f["field"], f["operator"], f["value"])
        if key not in seen:
            seen.add(key)
            unique_filters.append(f)

    dsl["filters"] = unique_filters

    # 🧠 STEP 7: FINAL CHECK
    if not dsl["filters"]:
        raise Exception("Could not understand query")

    return dsl