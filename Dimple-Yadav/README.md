# 📊 AI-Powered Stock Screener & Advisory Platform

## 🔎 Overview

AI-Powered Stock Screener is a backend-driven stock analysis system that allows users to query financial markets using natural language. The system interprets user intent, translates it into structured financial filters, and returns validated results through a lightweight interactive interface.

This project focuses on building an intelligent screening engine using LLMs, FastAPI, and a Streamlit-based frontend.

---

## 🧠 Core Idea

Instead of applying manual financial filters, users can type queries like:

> “Show technology companies with strong cash flow and low debt.”

The system:
1. Parses the natural language input
2. Converts it into structured filtering logic
3. Validates and executes safe queries
4. Returns filtered stock data

---

## 🏗️ Architecture

### Frontend
- **Streamlit**
  - Query Input Interface
  - Results Display (DataFrames / Tables)
  - Interactive UI Components
  - Rapid prototyping & testing

### Backend
- **FastAPI**
  - REST API endpoints
  - Query validation layer
  - LLM integration
  - Screener logic engine
  - Business rule enforcement

### AI Layer
- Large Language Model (LLM)
  - Natural Language → Structured JSON
  - Controlled output format
  - Schema validation before execution

### Data Layer (Pluggable)
- Financial dataset (CSV / DB)
- PostgreSQL (optional extension)
- Redis (future caching layer)

---

## ⚙️ Tech Stack

| Layer        | Technology |
|--------------|------------|
| Frontend     | Streamlit |
| Backend      | FastAPI |
| AI Engine    | OpenAI / Azure OpenAI |
| Data Storage | PostgreSQL / CSV (initial phase) |
| Language     | Python |

---

## 🔄 System Workflow

1. User enters query in Streamlit UI.
2. Request sent to FastAPI endpoint.
3. Backend sends query to LLM for structured parsing.
4. LLM returns validated JSON conditions.
5. Screener engine applies conditions to dataset.
6. Filtered results returned to frontend.
7. Streamlit renders results dynamically.

---

## 📌 Example Natural Language Queries

- “Show companies with consistent profits and low loan burden.”
- “Find technology stocks growing steadily every year.”
- “Which companies look undervalued compared to their performance?”
- “Show companies where founders still hold a strong stake.”

---

## 🧪 API Design (Sample Endpoint)



Request Body:
```json
{
  "query": "Show companies with low debt and strong cash flow"
}

{
  "sector": "any",
  "conditions": [
    {"field": "debt_to_cashflow", "operator": "<", "value": 3}
  ]
}
