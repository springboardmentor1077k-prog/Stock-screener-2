import json
import os


def save_structured_data(symbol: str, source: str, structured_data: dict):
    os.makedirs("data/structured", exist_ok=True)

    filename = f"{symbol}_{source}_structured.json"
    filepath = os.path.join("data/structured", filename)

    with open(filepath, "w") as f:
        json.dump(structured_data, f, indent=4)

    print(f"Structured data saved to {filepath}")
    