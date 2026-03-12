# SQL Compiler Project

This project implements a Python SQL compiler that converts DSL queries into parameterized SQL queries.

Architecture Flow:

User Query
↓
DSL Query
↓
SQL Compiler
↓
SQL Query + Parameters

Features:

- Field to column mapping
- AND / OR logic support
- Parameterized SQL queries
- Safe query generation

Example DSL Query

{
 "conditions":[
  {"field":"pe_ratio","operator":"<","value":15}
 ],
 "logic":"AND"
}

Generated SQL

SELECT * FROM companies WHERE companies.pe_ratio < %s

Parameters

[15]

Run the Program

python sql_compiler.py