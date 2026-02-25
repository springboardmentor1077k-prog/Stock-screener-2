# Stock Market Data Pipeline – Layered Architecture

## Overview

This project implements a layered data ingestion pipeline to fetch, process, and store stock market data using market APIs (Yahoo Finance).

The system follows a **Layered Model (LM)** to ensure clean separation of concerns and modularity.

---

# High-Level Architecture (Layered Model)



---

# Layer Descriptions

## 1️. Orchestrator Layer  
**File:** `pipeline_runner.py`

**Responsibilities:**
- Controls execution flow
- Calls API clients
- Invokes parsers
- Builds structured output
- Manages execution flags

This layer coordinates the entire pipeline but does not implement API logic or parsing logic.

---

## 2️. API Client Layer  
**Files:**
- `yahoo_client.py`
- `alpha_client.py`

**Responsibilities:**
- Communicates with external APIs
- Fetches raw JSON data
- Handles request failures and API errors

This layer strictly handles external communication.

---

## 3️. Raw Storage Layer  
**Folder:** `data/raw/`

**Responsibilities:**
- Stores untouched API responses
- Maintains snapshot history
- Enables reproducibility and debugging

Raw data is saved before any transformation.

---

## 4️. Parser Layer  
**Files:**
- `yahoo_parser.py`
- `alpha_parser.py`

**Responsibilities:**
- Extracts required metrics
- Removes unnecessary API noise
- Maps API-specific fields to internal structure

Example:
- `longName` → `name`
- `trailingPE` → `pe_ratio`

This layer standardizes API data into application-ready format.

---

## 5️. Structured Builder Layer  

**Responsibilities:**
- Builds domain-based schema:


  
This makes the system API-agnostic.

---

## 6️. Structured Storage Layer  
**Folder:** `data/structured/`

**Responsibilities:**
- Stores cleaned, structured JSON
- Provides final usable format for downstream systems

---

#  Full Data Flow

1. User runs `pipeline_runner.py`
2. API client fetches data
3. Raw JSON saved to `data/raw/`
4. Parser extracts relevant fields
5. Structured schema is built
6. Structured JSON saved to `data/structured/`

---

#  Key Design Principles

- Separation of concerns
- Modular architecture
- Snapshot-based raw storage
- API-agnostic structured output
- Scalable for future database integration

---

#  Future Extensions

- Multi-source normalization layer
- PostgreSQL integration
- Scheduled ingestion
- Retry/backoff mechanisms
- AI-based stock screener integration

---

# Conclusion

The project demonstrates a clean layered architecture for market data ingestion, ensuring maintainability, modularity, and extensibility for future development.
