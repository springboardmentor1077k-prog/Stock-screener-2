AI-Powered Mobile Stock Screener and Advisory Platform
📌 Project Overview

The AI-Powered Mobile Stock Screener and Advisory Platform is a smart financial application designed to help users analyze stocks, screen companies based on financial parameters, and receive AI-driven insights.

The platform allows users to enter natural language queries (for example: “Show companies with PE ratio < 20”) and converts them into structured database queries to fetch relevant stock data.

This project aims to simplify stock market analysis by combining Artificial Intelligence, FastAPI backend services, and an interactive frontend interface.

🎯 Objectives

Provide an AI-based stock screening system

Allow users to query stock data using natural language

Generate SQL queries automatically

Display filtered stock results quickly

Provide advisory insights for better investment decisions

🏗️ System Architecture

The system consists of the following main components:

User Interface (Frontend)
Built using Streamlit to provide an interactive dashboard for users.

Backend API Layer
Developed using FastAPI to process user queries and communicate with the database.

Query Compiler Module
Converts natural language queries into SQL queries using mapping dictionaries.

Database Layer
Stores stock market data and financial metrics.

AI Processing Layer
Interprets user input and generates structured queries.

⚙️ Technologies Used
Programming Language

Python

Backend Framework

FastAPI

Frontend

Streamlit

Database

PostgreSQL

Libraries

pandas

psycopg2

SQLAlchemy

uvicorn

Version Control

Git & GitHub

📂 Project Structure
AI-Stock-Screener
│
├── backend
│   ├── main.py
│   ├── compiler
│   │   ├── query_compiler.py
│   │   └── mapping_dictionary.py
│   ├── database
│   │   └── db_connection.py
│   └── models
│
├── frontend
│   └── streamlit_app.py
│
├── requirements.txt
└── README.md
🚀 Features

Natural language stock queries

Automatic SQL query generation

Fast API-based backend

Interactive Streamlit dashboard

Financial ratio filtering

Stock screening system

Modular and scalable architecture



SELECT company_name, pe_ratio
FROM companies
WHERE pe_ratio < 20;
