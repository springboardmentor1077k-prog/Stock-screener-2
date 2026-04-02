# app/services/llm_service.py (updated)

import json
from groq import Groq
from app.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

# System prompt for stock screener queries
SCREENER_PROMPT = """
You are a strict JSON DSL generator for stock screening.

Return ONLY valid JSON in this format:
{
  "type": "screener",
  "logic": "AND",
  "conditions": [
    {"field": "sector", "operator": "=", "value": "IT"},
    {"field": "pe_ratio", "operator": "<", "value": 20}
  ],
  "limit": 10
}

Allowed fields: sector, pe_ratio, peg_ratio, debt_fcf, promoter_holding, revenue, ebitda
Allowed operators: =, <, >, <=, >=, !=
"""

# New prompt for portfolio commands
PORTFOLIO_PROMPT = """
You are a portfolio management assistant. Convert user commands into structured JSON.

Return ONLY valid JSON in one of these formats:

For BUY commands:
{
  "type": "buy",
  "symbol": "AAPL",
  "quantity": 10,
  "price": 150.00,
  "notes": "Initial investment"
}

For SELL commands:
{
  "type": "sell",
  "symbol": "MSFT",
  "quantity": 5,
  "price": 330.25,
  "notes": "Partial profit booking"
}

For VIEW commands:
{
  "type": "view_portfolio"
}

For SUMMARY commands:
{
  "type": "portfolio_summary"
}

For TRANSACTIONS commands:
{
  "type": "view_transactions",
  "limit": 10
}

For WATCHLIST commands:
{
  "type": "watchlist_add",
  "symbol": "NVDA",
  "alert_price": 900.00,
  "notes": "AI leader"
}

Examples:
- "Buy 10 Apple shares at $150" → {"type": "buy", "symbol": "AAPL", "quantity": 10, "price": 150}
- "Sell 5 Microsoft shares" → {"type": "sell", "symbol": "MSFT", "quantity": 5}
- "Show my portfolio" → {"type": "view_portfolio"}
- "What's my portfolio value?" → {"type": "portfolio_summary"}
- "Add NVIDIA to watchlist with alert at $900" → {"type": "watchlist_add", "symbol": "NVDA", "alert_price": 900}

Do not include explanation. Return ONLY the JSON.
"""

def detect_query_type(query: str) -> str:
    """Detect if query is screener or portfolio command"""
    portfolio_keywords = [
        'buy', 'sell', 'portfolio', 'watchlist', 'my stocks', 
        'holdings', 'transaction', 'invested', 'profit', 'loss'
    ]
    query_lower = query.lower()
    for keyword in portfolio_keywords:
        if keyword in query_lower:
            return "portfolio"
    return "screener"

def generate_dsl(query: str):
    """Generate DSL for stock screener queries"""
    print("Calling LLM for screener query:", query)
    
    response = client.chat.completions.create(
        model=settings.MODEL_NAME,
        messages=[
            {"role": "system", "content": SCREENER_PROMPT},
            {"role": "user", "content": query}
        ],
        temperature=0
    )
    
    content = response.choices[0].message.content
    print("LLM RAW OUTPUT:", content)
    
    # Clean the response
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "")
    elif content.startswith("```"):
        content = content.replace("```", "")
    
    return json.loads(content)

def generate_portfolio_command(query: str):
    """Generate portfolio command from natural language"""
    print("Calling LLM for portfolio command:", query)
    
    response = client.chat.completions.create(
        model=settings.MODEL_NAME,
        messages=[
            {"role": "system", "content": PORTFOLIO_PROMPT},
            {"role": "user", "content": query}
        ],
        temperature=0
    )
    
    content = response.choices[0].message.content
    print("LLM RAW OUTPUT:", content)
    
    # Clean the response
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "")
    elif content.startswith("```"):
        content = content.replace("```", "")
    
    return json.loads(content)