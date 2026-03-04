# Stock-screener-2
## Week 3: LLM Integration & DSL Validation Architecture

This module implements a safe pipeline bridging natural language queries and strict system requirements. 

### Validation Strategy & Guardrails
To ensure the backend remains the decision-making authority, the LLM output is treated as untrusted input and parsed through strict Pydantic guardrails:

1. **Field Whitelist:** Only predefined financial metrics (e.g., `pe_ratio`, `debt`, `ebitda`) are allowed. Any unsupported metric is rejected.
2. **Operator Whitelist:** Only strict mathematical operators (`<`, `>`, `<=`, `>=`, `=`) are permitted.
3. **Logic Validation:** Logical groupings are strictly limited to `AND` or `OR`.
4. **Structure Constraints:** The query must contain a non-empty list of conditions, limited to a maximum number of conditions to prevent overly complex queries.
5. **Error Handling:** Any violation of these guardrails results in a structured JSON error response. The system is designed to fail gracefully without crashing or exposing internal stack traces.