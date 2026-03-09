from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

def execute_query(sql: str, params: dict):
    with engine.connect() as conn:
        result = conn.execute(text(sql), params)
        return [dict(row._mapping) for row in result]