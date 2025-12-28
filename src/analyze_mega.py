import os
import sys
import csv
import re
from collections import Counter

sys.path.append("src")
from common import parse_date  # noqa: E402

MEGA_CSV = "data/nj/mega_millions.csv"


def normalize_multiplier(m: str) -> str:
    """
    Normalize multiplier values.
    Examples:
      "2"  -> "2X"
      "2X" -> "2X"
      "" / "N/A" -> "N/A"
    """
    if not m:
        return "N/A"
    m = m.strip().upper()
    if m in ("NA", "N/A", "NONE"):
        return "N/A"
    # extract digits and convert to "nX"
    digits = re.findall(r"\d+", m)
    if not digits:
        return "N/A"
    return f"{digits[0]}X"


def read_mega_draws(csv_file):
    draws = []
    with open(csv_file, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            white_str = (row.get("white_numbers") or "").strip()
            mb_str = (row.get("mega_ball") or "").strip()
            d = (row.get("draw_date") or "").strip()
            mult = normalize_multiplier(row.get("multiplier", "N/A"))

            if not white_str or not mb_str or not d:
                continue

            try:
                white = list(map(int, white_str.split()))
                mega_ball = int(mb_str)
            except Exception:
                continue

            draws.append((d, white, mega_ball, mult))

    return draws


def main():
    print("\n===== MEGA MILLIONS =====")
    print("Looking for:", MEGA_CSV)
    print("Exists?:", os.path.exists(MEGA_CSV))

    if not os.path.exists(MEGA_CSV):
        print("❌ ERROR: mega_millions.csv not found.")
        print("✅ Fix: Ensure src/fetch_nj_latest.py runs and saves to data/nj/mega_millions.csv")
        return

    draws = read_mega_draws(MEGA_CSV)

    print(f"Total draws loaded: {len(draws)}")
    if not draws:
        print("❌ No data found — check CSV generation (headers/values).")
        return

    draws.sort(key=lambda x: parse_date(x[0]), reverse=True)

    print("\nLatest 10 draws")
    print("-" * 60)
    for d, w, mb, m in draws[:10]:
        print(f"{d} | White: {' '.join(map(str, w))} | MB: {mb} | Multiplier: {m}")

    white_all, mega_all, mult_all = [], [], []
    for _, w, mb, m in draws:
        white_all.extend(w)
        mega_all.append(mb)
        mult_all.append(m)

    print("\nWHITE BALL FREQUENCY (1–70)")
    print("-" * 40)
    white_freq = Counter(white_all)
    for i in range(1, 71):
        print(f"{i:2d} -> {white_freq.get(i, 0)} times")

    print("\nMEGA BALL FREQUENCY (1–25)")
    print("-" * 40)
    mega_freq = Counter(mega_all)
    for i in range(1, 26):
        print(f"{i:2d} -> {mega_freq.get(i, 0)} times")

    print("\nMULTIPLIER FREQUENCY")
    print("-" * 40)
    mult_freq = Counter(mult_all)
    for k in sorted(mult_freq.keys()):
        print(f"{k} -> {mult_freq[k]} times")


if __name__ == "__main__":
    main()
