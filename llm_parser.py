import json
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def parse_natural_language_to_dsl(user_query: str) -> dict:

    prompt = f"""
You are a strictly constrained parser.

Convert the natural language query into DSL JSON.

Rules:
1. Output MUST be JSON only
2. Allowed fields: pe_ratio, debt, market_cap, revenue, ebitda, promoter_holding
3. Allowed operators: <, >, <=, >=, =
4. Logic must be AND or OR

Example:

{{
 "conditions":[
   {{"field":"pe_ratio","operator":"<","value":20}}
 ],
 "logic":"AND"
}}

User Query: "{user_query}"
"""

    model = genai.GenerativeModel("gemini-2.5-flash")

    response = model.generate_content(prompt)

    clean_json = response.text.replace("```json", "").replace("```", "").strip()

    return json.loads(clean_json)