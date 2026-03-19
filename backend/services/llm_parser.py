import json
import re
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

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
    pe_match = re.search(r"pe\s*ratio\s*(less than|<)\s*(\d+)", query)
    if pe_match:
        conditions.append({
            "field": "pe_ratio",
            "operator": "<",
            "value": int(pe_match.group(2))
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
    # GROWTH DETECTION
    # -----------------------------
    if "growth" in query or "increase" in query:

        if "price" in query:
            field = "price_growth"
        else:
            field = "price_growth"

        if "greater than" in query or "more than" in query:
            operator = ">"
        elif "less than" in query:
            operator = "<"
        else:
            operator = ">"

        match = re.search(r"\d+\.?\d*", query)

        if match:
            value = float(match.group())

            # convert % to decimal
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
    if "it" in words or "technology" in words:
        conditions.append({
            "field": "sector",
            "operator": "=",
            "value": "Technology"
        })

    if "bank" in words or "banking" in words:
        conditions.append({
            "field": "sector",
            "operator": "=",
            "value": "Financial Services"
        })

    if "pharma" in words or "healthcare" in words:
        conditions.append({
            "field": "sector",
            "operator": "=",
            "value": "Healthcare"
        })

    # -----------------------------
    # TIME FILTER 
    # -----------------------------
    if "last year" in query:
        time_filter = "last_year"

    elif "6 month" in query:
        time_filter = "last_6_months"

    elif "last 4 quarters" in query:
        time_filter = "last_4_quarters"

    elif "recent" in query:
        time_filter = "recent_quarters"

    # -----------------------------
    # Default condition
    # -----------------------------
    if not conditions:
        conditions.append({
            "field": "pe_ratio",
            "operator": "<",
            "value": 30
        })

    return {
        "conditions": conditions,
        "logic": "AND",
        "time_filter": time_filter
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