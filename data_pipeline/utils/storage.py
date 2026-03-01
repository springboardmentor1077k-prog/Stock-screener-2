import json
import os
from datetime import datetime


def save_raw_data(source: str, symbol: str, data: dict):
    """
    Saves raw API response to data/raw directory.
    """

    if data is None:
        print("No data to save.")
        return

    os.makedirs("data/raw", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{symbol}_{source}_{timestamp}.json"
    filepath = os.path.join("data/raw", filename)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Saved raw data to {filepath}")


def load_latest_raw(symbol: str, source: str):
    """
    Load the most recent raw snapshot for a given symbol and source.
    Example source: 'alpha_daily' or 'alpha_overview'
    """

    folder = "data/raw"
    if not os.path.exists(folder):
        return None

    files = [
        f for f in os.listdir(folder)
        if f.startswith(f"{symbol}_{source}")
    ]

    if not files:
        return None

    files.sort(reverse=True)
    latest_file = files[0]

    filepath = os.path.join(folder, latest_file)

    with open(filepath, "r") as f:
        return json.load(f)