# AI-Powered Stock Screener Backend

## Overview

This project implements the backend of an **AI-powered stock screener** that enables users to query financial data using **natural language**.

Instead of manually writing complex database filters, users can simply ask queries such as:

> "Show companies with PE ratio less than 25."

The backend processes these queries using a **Large Language Model (LLM)**, converts them into a structured query format, validates them using guardrails, compiles them into SQL, executes them on the database, and returns structured results.

This system demonstrates how **AI-driven query interpretation can be integrated with traditional database systems** to enable natural language access to financial datasets.

The project is part of an **AI-Powered Mobile Stock Screener and Advisory Platform**, which aims to help investors analyze stock data using AI-assisted insights and analytics.

---

## Sprint 1 — API & Database Foundation

The first sprint focused on establishing the **data ingestion and storage infrastructure** required for the stock screener.

### Key tasks completed

- Integrated a **market data API** to retrieve company information, fundamentals, and historical stock data.
- Stored retrieved API responses in **structured JSON datasets**.
- Designed and implemented the **database schema** for storing financial metrics and company information.
- Created scripts to **initialize and populate the SQLite database** used for stock screening queries.

This stage established the **data layer required for the AI screening engine**.

---

## Sprint 2 — LLM Screener Engine

Sprint 2 implemented the **AI query processing pipeline**, enabling natural language queries to be transformed into secure database queries.

### Implemented modules

- FastAPI backend  
- LLM parser module  
- DSL schema and validation  
- SQL compiler  
- Query execution module  
- Result formatting logic  

---

## System Architecture

```
Natural Language Query
        ↓
LLM Parser
        ↓
DSL Validation
        ↓
SQL Compiler
        ↓
Database Execution
        ↓
Result Formatting
        ↓
API JSON Response
```

This layered architecture ensures queries are **validated, secure, and executable before interacting with the database**.

---

## Guardrails & Validation Strategy

Because LLM outputs may be unreliable, the system treats them as **untrusted input** and validates them using strict guardrails.

### Field Whitelist

Only predefined financial metrics are allowed.

Examples:

- `pe_ratio`
- `revenue`
- `ebitda`
- `promoter_holding`

### Operator Whitelist

Supported comparison operators:

```
<  >  <=  >=  =
```

### Logical Constraints

Conditions can only be combined using:

```
AND / OR
```

### Structure Validation

Queries must follow the defined **DSL schema** and include valid conditions.

### Error Handling

Invalid queries return **structured JSON error responses** instead of executing unsafe operations.

---

## DSL Structure

The system uses a **Domain Specific Language (DSL)** as an intermediate representation between the LLM output and SQL execution.

### Example DSL

```json
{
  "conditions": [
    {
      "field": "pe_ratio",
      "operator": "<",
      "value": 25
    }
  ],
  "logic": "AND"
}
```

This structure enables **strict validation and safe translation into SQL queries**.

---

## SQL Compilation Strategy

Validated DSL queries are translated into SQL using a **custom compiler**.

### Example

**DSL Condition**

```
pe_ratio < 25
```

**Compiled SQL**

```sql
SELECT * FROM fundamentals WHERE pe_ratio < ?
```

The system uses **parameterized queries (`?`)** to prevent SQL injection by separating query logic from user input.

---

## Query Execution & Result Formatting

The execution layer performs the following steps:

1. Connects to the SQLite database  
2. Executes parameterized SQL queries  
3. Retrieves matching records  
4. Converts database rows into JSON objects  

### Example API Response

```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "pe_ratio": 22.5,
      "revenue": 45000,
      "ebitda": 15000
    }
  ]
}
```

---

## Example End-to-End Query

### Endpoint

```
POST /query
```

### Example Request

```json
{
  "query": "show companies with pe_ratio less than 25"
}
```

### Execution Steps

1. Natural language query parsed by the LLM  
2. Converted into DSL format  
3. Validated using Pydantic guardrails  
4. Compiled into SQL  
5. Executed against the database  
6. Returned as structured JSON results  

---

## Running the Backend

### Install dependencies

```bash
pip install fastapi uvicorn google-generativeai python-dotenv
```

### Create a `.env` file in the project root

```
GOOGLE_API_KEY=your_api_key
```

### Start the server

```bash
python -m uvicorn main:app --reload
```

### Open API documentation

```
http://127.0.0.1:8000/docs
```

---

## Tech Stack

### Backend
- FastAPI
- Python
- SQLite

### AI Integration
- Gemini / LLM parser

### Data Processing
- Pydantic validation
- Custom SQL compiler