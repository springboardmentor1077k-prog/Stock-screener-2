import json
import re
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("⚠️ GOOGLE_API_KEY not found — using fallback parser")

genai.configure(api_key=API_KEY)


def extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in LLM response")

    json_str = match.group()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON returned by LLM")


# -----------------------------
# FALLBACK RULE-BASED PARSER
# -----------------------------
def fallback_parser(query: str) -> dict:

    query = query.lower()
    words = re.findall(r"\b\w+\b", query)

    conditions = []
    time_filter = None

    # -----------------------------
    # PE ratio
    # -----------------------------
    pe_match = re.search(r"(pe|pe ratio)\s*(less than|<)\s*(\d+)", query)
    if pe_match:
        conditions.append({
            "field": "pe_ratio",
            "operator": "<",
            "value": int(pe_match.group(3))
        })

    pe_match2 = re.search(r"(pe|pe ratio)\s*(greater than|>|more than)\s*(\d+)", query)
    if pe_match2:
        conditions.append({
            "field": "pe_ratio",
            "operator": ">",
            "value": int(pe_match2.group(3))
        })

    # -----------------------------
    # Revenue
    # -----------------------------
    rev_match = re.search(r"revenue\s*(greater than|>)\s*(\d+)", query)
    if rev_match:
        conditions.append({
            "field": "revenue",
            "operator": ">",
            "value": int(rev_match.group(2))
        })

    # -----------------------------
    # EBITDA
    # -----------------------------
    ebitda_match = re.search(r"ebitda\s*(greater than|>)\s*(\d+)", query)
    if ebitda_match:
        conditions.append({
            "field": "ebitda",
            "operator": ">",
            "value": int(ebitda_match.group(2))
        })

    # -----------------------------
    # Profit Margin
    # -----------------------------

    pm_match = re.search(r"profit\s*margin\s*(greater than|>|more than)\s*(\d+)", query)
    if pm_match:
        conditions.append({
            "field": "profit_margin",
            "operator": ">",
            "value": float(pm_match.group(2)) / 100
        })

    pm_match2 = re.search(r"profit\s*margin\s*(less than|<)\s*(\d+)", query)
    if pm_match2:
        conditions.append({
            "field": "profit_margin",
            "operator": "<",
            "value": float(pm_match2.group(2)) / 100
        })

    # -----------------------------
    # GROWTH DETECTION
    # -----------------------------
    if "growth" in query or "increase" in query or "grew" in query:

        # Field detection
        if "price" in query:
            field = "price_growth"
        else:
            field = "price_growth"

        # Operator detection
        if "greater than" in query or "more than" in query or "above" in query:
            operator = ">"
        elif "less than" in query or "below" in query:
            operator = "<"
        else:
            operator = ">"  # default

        # Extract percentage number
        match = re.search(r"\d+\.?\d*", query)
        if match:
            value = float(match.group())

            # Convert percentage to decimal
            if value > 1:
                value = value / 100

            conditions.append({
                "field": field,
                "operator": operator,
                "value": value
            })


    # -----------------------------
    # Sector detection
    # -----------------------------
    if "it" in words or "technology" in words or "tech" in words:
        conditions.append({"field": "sector", "operator": "=", "value": "Technology"})

    elif "bank" in words or "banking" in words or "financial" in words:
        conditions.append({"field": "sector", "operator": "=", "value": "Financial Services"})

    elif "pharma" in words or "healthcare" in words or "hospital" in words:
        conditions.append({"field": "sector", "operator": "=", "value": "Healthcare"})

    elif "energy" in words or "oil" in words or "gas" in words:
        conditions.append({"field": "sector", "operator": "=", "value": "Energy"})

    elif "consumer defensive" in query:
        conditions.append({"field": "sector", "operator": "=", "value": "Consumer Defensive"})

    elif "consumer cyclical" in query or "auto" in words:
        conditions.append({"field": "sector", "operator": "=", "value": "Consumer Cyclical"})

    elif "materials" in words or "chemicals" in words:
        conditions.append({"field": "sector", "operator": "=", "value": "Basic Materials"})

    elif "telecom" in words or "communication" in words:
        conditions.append({"field": "sector", "operator": "=", "value": "Communication Services"})

    # -----------------------------
    # TIME FILTER 
    # -----------------------------
    if "last year" in query or "past year" in query:
        time_filter = "last_year"

    elif "6 month" in query or "last 6 months" in query:
        time_filter = "last_6_months"

    elif "last 4 quarters" in query or "past 4 quarters" in query:
        time_filter = "last_4_quarters"

    elif "recent" in query or "latest" in query:
        time_filter = "recent_quarters"


    # SORT FIELD DETECTION
    if "market cap" in query:
        sort_by = "market_cap"
    elif "revenue" in query:
        sort_by = "revenue"
    elif "profit margin" in query:
        sort_by = "profit_margin"
    else:
        sort_by = "pe_ratio"

    # -----------------------------
    # TOP N DETECTION
    # -----------------------------
    top_match = re.search(r"top\s+(\d+)", query)
    limit = None

    if top_match:
        limit = int(top_match.group(1))

    # -----------------------------
    # Default condition
    # -----------------------------
    # If no numeric conditions, allow sector-only queries
    if not conditions:
        conditions = []
    return {
        "conditions": conditions,
        "logic": "AND",
        "time_filter": time_filter,
        "limit": limit,
        "sort_by": sort_by
    }


# -----------------------------
# MAIN LLM PARSER
# -----------------------------
def parse_natural_language_to_dsl(user_query: str) -> dict:

    prompt = f"""
You are an AI that converts stock screener queries into DSL JSON.

STRICT RULES:
- Output ONLY JSON
- No explanation
- No markdown
- No comments

Allowed fields:
pe_ratio
peg_ratio
market_cap
revenue
revenue_growth
ebitda
profit_margin
roe
roa
debt_to_equity
eps
book_value
dividend_yield
sector
price_growth

Allowed operators:
< > <= >= =

Logic values:
AND OR

Allowed time filters:
last_year
last_4_quarters
recent_quarters
last_6_months

User Query:
{user_query}
"""

    try:
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config={"temperature": 0}
        )

        response = model.generate_content(prompt)

        if not response or not response.text:
            raise ValueError("Empty response from Gemini")

        dsl_json = extract_json(response.text)

        return dsl_json

    except Exception as e:
        print("Gemini failed, using fallback parser:", str(e))
        return fallback_parser(user_query)