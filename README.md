# AI-Powered Stock Screener and Advisory Platform

## Overview

The AI-Powered Stock Screener and Advisory Platform is a full-stack application designed to help retail and professional investors make data-driven investment decisions using natural language queries, financial analytics, and AI-powered insights.

The platform allows users to screen stocks using plain English queries, track their portfolio performance, manage watchlists, create alerts, and analyze market data through interactive dashboards. The system uses Large Language Models (LLMs) to interpret user queries, convert them into structured logic, execute them on financial datasets, and return actionable insights.

This project demonstrates how AI can be integrated with financial data systems to build an intelligent stock analysis and advisory platform.

---

## Key Features

### 1. AI Stock Screener

* Natural language query interface
* LLM converts user query → DSL → SQL
* Guardrails and validation for safe query execution
* Dynamic filtering using financial metrics (PE, ROE, Revenue, EBITDA, etc.)
* Returns structured stock insights

### 2. AI Advisory & Insights

* Provides data-driven stock insights
* Financial metric analysis
* Portfolio performance insights
* Market trend and performance visualization
* Decision-support analytics for investors

### 3. Portfolio Management

* Add stocks to portfolio
* Remove stocks from portfolio
* Track investment value, current value, and profit/loss
* Portfolio allocation breakdown
* Portfolio growth visualization
* Return percentage calculation

### 4. Watchlist Management

* Add stocks to watchlist
* Remove stocks from watchlist
* Track selected stocks

### 5. Alerts & Notifications

* Create alerts based on financial conditions
* Trigger alerts when screening conditions are met
* Store and manage alert rules

### 6. Community Module

* Users can post and share investment ideas
* Discussion system for stocks and strategies

### 7. Market Data Integration

* Fetch company fundamentals and stock prices
* Store historical stock data
* Used for screening, portfolio tracking, and analytics

---

## System Architecture

The platform follows a layered AI + Data architecture:

```
User (Natural Language Query)
            ↓
        LLM Parser
            ↓
        DSL Validator
            ↓
        SQL Compiler
            ↓
        Database Execution
            ↓
        Analytics Engine
            ↓
        API Response
            ↓
        Frontend Dashboard
```

This architecture ensures secure query execution, validated AI outputs, and reliable financial analytics.

---

## Database Schema (Main Tables)

| Table              | Description               |
| ------------------ | ------------------------- |
| symbols            | Company basic information |
| fundamentals       | Financial metrics         |
| historical_metrics | Historical stock prices   |
| users              | User accounts             |
| portfolio          | User holdings             |
| watchlist          | Saved stocks              |
| alerts             | Alert conditions          |
| search_history     | Query history             |
| posts              | Community posts           |

---

## Tech Stack

### Backend

* FastAPI
* Python
* SQLite
* Redis (Caching)

### Frontend

* Streamlit

### AI Integration

* Gemini / LLM API
* DSL Query Parser
* SQL Compiler

### Data Source

* Yahoo Finance API (yfinance)

---

## How to Run the Project

### Install Dependencies

```
pip install fastapi uvicorn streamlit yfinance pandas plotly python-dotenv
```

### Setup Environment Variables

Create `.env` file:

```
GOOGLE_API_KEY=your_api_key
```

### Create Database

```
python backend/database/create_db.py
```

### Fetch Market Data

```
python backend/ingestion/yfinance_fetch.py
python backend/ingestion/ingest_api_data.py
```

### Run Backend

```
python -m uvicorn backend.main:app --reload
```

### Run Frontend

```
streamlit run frontend/app.py
```

---

## Example Natural Language Queries

* Show companies with PE ratio less than 20
* Find companies with revenue growth above 10%
* Show companies with high ROE and low debt
* Find undervalued IT stocks
* Show stocks with strong fundamentals and positive earnings
