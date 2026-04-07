# AI-Powered Stock Screener

## Project Overview
This project is an AI-driven stock screening tool that allows users to query financial data using natural language. The backend processes these queries, validates them, and securely fetches data from the database.

## Week 1 & 2: API Design & Database Architecture
* Designed the core database schema including `Symbols`, `Fundamentals`, and `Historical Metrics` tables.
* Documented the API architecture and researched JWT authentication and Redis caching mechanisms for secure and fast data retrieval.

## Week 3: LLM Integration & DSL Validation Architecture
This module implements a safe pipeline bridging natural language queries and strict system requirements. 

### Validation Strategy & Guardrails
To ensure the backend remains the decision-making authority, the LLM output is treated as untrusted input and parsed through strict Pydantic guardrails:
1. **Field Whitelist:** Only predefined financial metrics (e.g., `pe_ratio`, `debt`, `ebitda`) are allowed. Any unsupported metric is rejected.
2. **Operator Whitelist:** Only strict mathematical operators (`<`, `>`, `<=`, `>=`, `=`) are permitted.
3. **Logic Validation:** Logical groupings are strictly limited to `AND` or `OR`.
4. **Structure Constraints:** The query must contain a non-empty list of conditions, limited to a maximum number of conditions to prevent overly complex queries.
5. **Error Handling:** Any violation of these guardrails results in a structured JSON error response. The system is designed to fail gracefully without crashing or exposing internal stack traces.

## Sprint 2: Execution Layer & End-to-End Pipeline
This section documents the completion of the Sprint-2 deliverables, which successfully transforms natural language queries into safe, executable database operations.

### 1. System Architecture
The backend follows a strict, layered pipeline to ensure accurate and secure query execution. The end-to-end flow is designed as follows:
1. **Natural Language Query:** User provides unstructured text.
2. **LLM Parser:** Extracts conditions and outputs a structured JSON DSL.
3. **DSL Validation:** Pydantic guardrails enforce whitelists and structural integrity.
4. **SQL Compiler:** Translates the valid DSL into an executable query.
5. **Database Execution:** Executes the query securely on the SQLite/PostgreSQL database.
6. **Result Formatting:** Transforms database rows into a structured API JSON response.

### 2. DSL Structure
The Domain Specific Language (DSL) acts as the secure intermediary between the LLM and the database. It is strictly validated using Pydantic models with the following constraints:
* **Allowed Fields:** Limited to predefined financial metrics (`pe_ratio`, `debt`, `market_cap`, `revenue`, `ebitda`, `promoter_holding`).
* **Allowed Operators:** Restricted to logical and mathematical comparisons (`<`, `>`, `<=`, `>=`, `=`).
* **Logical Connectors:** Queries must be grouped using `AND` or `OR`.

### 3. SQL Compilation Strategy
To prevent SQL injection and ensure deterministic execution, the compiler maps the validated DSL to database queries using parameterized execution.
* **No Direct Concatenation:** User input is strictly separated from the query structure.
* **Parameterized Queries:** We utilize parameterized placeholders (`?` or `%s`) for all dynamically injected values.

### 4. Testing Results
The end-to-end pipeline was successfully tested using the `/query` endpoint. 
* **Input Query:** `"Show me companies with pe_ratio less than 20"`
* **Compiler Output:** `SELECT * FROM fundamentals WHERE pe_ratio < ?`
* **API Response:** The database results were successfully converted from tuples into a structured dictionary format, handling errors gracefully without exposing internal stack traces.