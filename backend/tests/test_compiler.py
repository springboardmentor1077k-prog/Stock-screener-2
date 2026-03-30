from backend.services.compiler import compile_dsl_to_sql

def test_basic_sql_generation():
    dsl = {
        "conditions": [
            {"field": "pe_ratio", "operator": "<", "value": 20}
        ],
        "logic": "AND"
    }

    sql, params = compile_dsl_to_sql(dsl, sort_by="pe_ratio", order="descending")

    assert "WHERE" in sql
    assert "pe_ratio < ?" in sql
    assert "ORDER BY f.pe_ratio DESC" in sql
    assert params == [20]


def test_price_growth_join():
    dsl = {
        "conditions": [
            {"field": "price_growth", "operator": ">", "value": 10}
        ]
    }

    sql, params = compile_dsl_to_sql(dsl)

    assert "JOIN price_growth" in sql
    assert "growth.price_growth > ?" in sql