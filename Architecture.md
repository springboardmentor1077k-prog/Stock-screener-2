# AI-Powered Stock Screener  
## Sprint-2 Architecture Documentation

This document describes the architecture implemented for the **Natural Language → DSL → SQL pipeline** in the AI-Powered Stock Screener backend.

The objective of this milestone was to build a **controlled LLM interface** that allows users to query financial data using natural language while maintaining **database safety and architectural discipline**.

---

# 1. System Architecture

The system implements a **layered pipeline architecture** that converts natural language queries into safe SQL queries.

The implemented flow is:

```
User Natural Language Query
            │
            ▼
FastAPI Endpoint (/query)
            │
            ▼
LLM Parser (Gemini API)
            │
            ▼
DSL JSON
            │
            ▼
DSL Validator
            │
            ▼
SQL Compiler
            │
            ▼
Query Execution Layer
            │
            ▼
PostgreSQL Database
            │
            ▼
Formatted JSON API Response
```

Each component in the pipeline performs a specific responsibility to ensure **security, validation, and structured query generation**.

---

# 2. FastAPI Backend

The backend is implemented using **FastAPI**.

The following route modules are included:

```
backend/routes/
    auth.py
    companies.py
    portfolio.py
    alerts.py
    query.py
```

The `/query` endpoint is responsible for executing the **Natural Language query pipeline**.

Example API request:

```json
POST /query

{
  "query": "technology companies with pe ratio less than 30"
}
```

---

# 3. LLM Parser Module

The **LLM Parser** converts the natural language query into a structured **Domain Specific Language (DSL)** format.

File:

```
backend/llm/parser.py
```

The parser uses the **Google Gemini API** to generate DSL output.

Example user query:

```
technology companies with pe ratio less than 30
```

LLM generated DSL:

```json
{
 "filters":[
    {
      "field":"sector",
      "operator":"=",
      "value":"technology"
    },
    {
      "field":"pe_ratio",
      "operator":"<",
      "value":30
    }
 ],
 "logic":"AND"
}
```

The parser removes markdown formatting or JSON prefixes returned by the LLM to ensure the output can be parsed correctly.

---

# 4. DSL Structure

The DSL (Domain Specific Language) defines a **structured representation of financial filters**.

Example DSL format:

```json
{
 "filters":[
  {
   "field":"sector",
   "operator":"=",
   "value":"Technology"
  },
  {
   "field":"pe_ratio",
   "operator":"<",
   "value":30
  }
 ],
 "logic":"AND"
}
```

### DSL Components

| Field | Description |
|------|-------------|
| filters | List of filtering conditions |
| field | Database attribute to filter |
| operator | Comparison operator |
| value | Filter value |
| logic | Logical condition joining filters |

Supported fields in the current implementation:

```
sector
pe_ratio
revenue
symbol
```

Supported operators:

```
= < > <= >=
```

Logical operators:

```
AND
OR
```

---

# 5. DSL Validation Layer

The DSL Validator ensures that the generated DSL is **safe and valid before SQL generation**.

File:

```
backend/dsl/validator.py
```

The validator checks:

- Allowed fields
- Allowed operators
- Allowed logical operators
- Presence of required DSL attributes

Example validation rules:

```python
ALLOWED_FIELDS = {
    "sector",
    "pe_ratio",
    "revenue",
    "symbol"
}
```

If an invalid field is detected, the system returns a controlled error response.

Example:

```
Invalid field: price
```

This prevents unsafe SQL generation.

---

# 6. SQL Compilation Strategy

The **SQL Compiler** converts DSL into parameterized SQL queries.

File:

```
backend/compiler/sql_compiler.py
```

The system uses a **field-to-column mapping dictionary**:

```python
FIELD_MAPPING = {
 "symbol": ("symbols","s.symbol"),
 "company_name": ("symbols","s.company_name"),
 "sector": ("symbols","s.sector"),
 "pe_ratio": ("fundamentals","f.pe_ratio"),
 "revenue": ("fundamentals","f.revenue")
}
```

Generated SQL example:

```sql
SELECT s.symbol, s.company_name
FROM symbols s
JOIN fundamentals f ON s.id = f.company_id
WHERE s.sector = %s AND f.pe_ratio < %s
```

SQL parameters:

```
["Technology", 30]
```

### Why parameterized SQL is used

Parameterized queries prevent **SQL injection attacks** by separating query structure from user data.

---

# 7. Query Execution Layer

The **execution module** runs the generated SQL against the PostgreSQL database.

File:

```
backend/execution/query_executor.py
```

Responsibilities:

- Execute compiled SQL
- Fetch database rows
- Convert tuples to dictionaries
- Format results for API responses

Example database result format:

```json
{
 "symbol": "AAPL",
 "company_name": "Apple Inc."
}
```

---

# 8. Result Formatting

The system returns results in a structured JSON response.

Example response format:

```json
{
 "dsl": {...},
 "sql": "...",
 "params": [...],
 "results": {
   "data":[
      {
        "symbol":"AAPL",
        "company_name":"Apple Inc."
      }
   ],
   "count":1
 }
}
```

The response also handles edge cases:

- empty results
- database execution errors
- invalid DSL queries

---

# 9. Testing Results

The system was tested using several natural language queries.

### Query 1

```
technology companies with pe ratio less than 30
```

Generated DSL:

```
sector = Technology
pe_ratio < 30
```

Generated SQL:

```sql
SELECT s.symbol, s.company_name
FROM symbols s
JOIN fundamentals f ON s.id = f.company_id
WHERE s.sector = %s AND f.pe_ratio < %s
```

---

### Query 2

```
companies with revenue greater than 100000000
```

Generated DSL:

```
revenue > 100000000
```

---

### Query 3

```
technology companies or companies with pe ratio less than 20
```

Generated DSL:

```
logic: OR
```

---

# 10. Key Architectural Features

The system ensures:

- Controlled LLM output
- Structured DSL representation
- Validation layer before SQL generation
- Parameterized SQL queries
- Graceful error handling
- Consistent API response formatting

These measures ensure the system remains **secure, reliable, and extensible** when integrating LLMs with database systems.

---

# Conclusion

The implemented architecture successfully demonstrates a **controlled Natural Language query system** using LLMs.

The pipeline ensures that user queries are converted into safe database queries through the following steps:

```
Natural Language
→ DSL
→ Validation
→ SQL Compilation
→ Database Execution
→ API Response
```

This approach enables flexible natural language querying while maintaining strict control over database access and query safety.

---

