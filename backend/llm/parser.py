import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def parse_query(user_query: str):

    prompt = f"""
You are a financial query parser.

Convert the following natural language query into DSL JSON format.

Return ONLY JSON. Do not include the word json or markdown.

DSL schema:

{{
 "filters":[
    {{
      "field":"sector | pe_ratio | revenue | symbol",
      "operator":"= | < | > | <= | >=",
      "value":"value"
    }}
 ],
 "logic":"AND | OR"
}}

User Query:
{user_query}
"""

    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=prompt
    )

    text_output = response.text.strip()

    # remove markdown if present
    if text_output.startswith("json"):
        text_output = text_output.replace("json", "", 1)

    if "```" in text_output:
        text_output = text_output.split("```")[1]

    text_output = text_output.strip()

    print("LLM RAW OUTPUT:", text_output)

    try:
        dsl = json.loads(text_output)
    except Exception:
        raise ValueError("LLM returned invalid JSON")

    return dsl