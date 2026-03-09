from app.services.compiler import compile_dsl_to_sql
from app.services.validator import validate_fields
from app.database.connection import execute_query
from app.schema.dsl_schema import DSL

def run_screener(dsl_raw):
    dsl = DSL(**dsl_raw)
    validate_fields(dsl)
    sql, params = compile_dsl_to_sql(dsl)
    return execute_query(sql, params)
