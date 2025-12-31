import csv
import os
from datetime import datetime


def parse_date(d: str, strict: bool = False) -> datetime:
    """
    Parse date safely.

    Supported formats:
      - YYYY-MM-DD
      - MM/DD/YYYY
      - YYYY-MM-DDTHH:MM:SS

    If strict=False (default):
      - returns None on failure instead of crashing
    """
    if not d:
        if strict:
            raise ValueError("Empty date value")
        return None

    d = d.strip()

    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(d, fmt)
        except ValueError:
            continue

    if strict:
        raise ValueError(f"Unrecognized date format: {d}")

    return None


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
