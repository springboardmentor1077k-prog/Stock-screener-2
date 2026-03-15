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


def parse_natural_language_to_dsl(user_query: str) -> dict:

    prompt = f"""
You are an AI that converts stock screener queries into DSL JSON.

STRICT RULES:
- Output ONLY JSON
- No explanation
- No markdown
- No comments

Allowed fields (these match database columns exactly):

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

Do NOT invent new fields.
Use only the fields listed above.

Growth interpretation examples:

"high growth companies" → revenue_growth > 0.1
"companies doing better every year" → revenue_growth > 0
"companies with increasing revenue" → revenue_growth > 0
"improving profits" → roe > 0.15

Price trend interpretation:

"stocks trending upward" → price_growth > 0
"stocks gaining momentum" → price_growth > 0
"stocks with rising price" → price_growth > 0

Sector examples:

"IT companies" → sector = "Technology"
"banking companies" → sector = "Financial Services"
"pharma companies" → sector = "Healthcare"

Allowed operators:
< > <= >= =

Logic values:
AND OR

JSON format:

{{
 "conditions":[
   {{
     "field":"pe_ratio",
     "operator":"<",
     "value":20
   }}
 ],
 "logic":"AND"
}}

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
        raise RuntimeError(f"LLM parsing failed: {str(e)}")