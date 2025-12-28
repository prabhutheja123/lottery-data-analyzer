import csv
import os
from datetime import datetime


def parse_date(d: str) -> datetime:
    """
    Parse date in either YYYY-MM-DD or MM/DD/YYYY format.
    """
    if not d:
        raise ValueError("Empty date value")

    try:
        return datetime.strptime(d, "%Y-%m-%d")
    except ValueError:
        return datetime.strptime(d, "%m/%d/%Y")


def read_csv(path: str):
    """
    Read CSV safely and return list of rows.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV file not found: {path}")

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print(f"⚠️ Warning: CSV exists but has no data rows -> {path}")

    return rows
