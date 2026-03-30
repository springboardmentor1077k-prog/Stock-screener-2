from llm import nl_to_dsl

query = "cheap stocks limit 5"

dsl = nl_to_dsl(query)

print(dsl)