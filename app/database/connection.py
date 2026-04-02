# app/database/connection.py
from sqlalchemy import create_engine, text
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create engine with proper configuration for SQLite
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Set to True to see SQL logs
)

def execute_query(sql: str, params: dict):
    """Execute parameterized query and return results"""
    try:
        # Convert named parameters to SQLite format if needed
        # SQLite uses :param format, which we already have
        
        with engine.connect() as conn:
            logger.debug(f"Executing: {sql}")
            logger.debug(f"With params: {params}")
            
            result = conn.execute(text(sql), params)
            
            # Convert to list of dicts
            rows = []
            for row in result:
                rows.append(dict(row._mapping))
            
            logger.info(f"Query returned {len(rows)} rows")
            return rows
            
    except Exception as e:
        logger.error(f"Query execution error: {e}")
        logger.error(f"SQL: {sql}")
        logger.error(f"Params: {params}")
        raise