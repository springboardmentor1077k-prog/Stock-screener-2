import json
import re
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# Configure Gemini
genai.configure(api_key=API_KEY)


def extract_json(text: str) -> dict:
    """
    Extract JSON object from LLM response safely.
    Handles cases where the model adds explanations or markdown.
    """

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
Convert the following natural language stock screener query into DSL JSON.

Rules:
- Return ONLY JSON
- No explanations
- No markdown

Allowed fields:
pe_ratio, peg_ratio, debt_fcf, revenue, ebitda, promoter_holding

Allowed operators:
<, >, <=, >=, =

Logic:
AND or OR

Example:

{{
 "conditions":[
   {{"field":"pe_ratio","operator":"<","value":20}}
 ],
 "logic":"AND"
}}

User Query:
{user_query}
"""

    try:

        model = genai.GenerativeModel("gemini-2.5-flash")

        response = model.generate_content(prompt)

        if not response or not response.text:
            raise ValueError("Empty response from Gemini")

        dsl_json = extract_json(response.text)

        return dsl_json

    except Exception as e:
        raise RuntimeError(f"LLM parsing failed: {str(e)}")