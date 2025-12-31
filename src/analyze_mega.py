import os
import sys
import csv
import re
from collections import Counter

sys.path.append("src")
from common import parse_date  # noqa: E402

MEGA_CSV = "data/nj/mega_millions.csv"


def normalize_multiplier(m: str) -> str:
    if not m:
        return "N/A"
    m = m.strip().upper()
    if m in ("NA", "N/A", "NONE"):
        return "N/A"
    digits = re.findall(r"\d+", m)
    if not digits:
        return "N/A"
    return f"{digits[0]}X"


def read_mega_draws(csv_file: str):
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
                if len(white) != 5:
                    continue
            except Exception:
                continue

            dt = parse_date(d)
            if dt is None:
                continue

            draws.append((d, dt, white, mega_ball, mult))

    return draws


def classify_bucket(freq: int, hot_min: int, med_min: int) -> str:
    if freq >= hot_min:
        return "HOT"
    if freq >= med_min:
        return "MEDIUM"
    return "COLD"


def top_n(counter: Counter, n: int = 10):
    return counter.most_common(n)


def main():
    print("\n===== MEGA MILLIONS =====")
    print("Looking for:", MEGA_CSV)
    print("Exists?:", os.path.exists(MEGA_CSV))

    if not os.path.exists(MEGA_CSV):
        print("❌ ERROR: mega_millions.csv not found.")
        print("✅ Fix: Ensure src/fetch_nj_latest.py runs and saves to data/nj/mega_millions.csv")
        return

    draws = read_mega_draws(MEGA_CSV)
    print("Valid draws parsed:", len(draws))

    if not draws:
        print("❌ No valid draws found — check CSV headers/values.")
        return

    draws.sort(key=lambda x: x[1], reverse=True)

    latest_d, _, latest_white, latest_mb, latest_mult = draws[0]

    print("\nLatest 10 draws")
    print("-" * 80)
    for d, _, w, mb, m in draws[:10]:
        print(f"{d} | White: {' '.join(map(str, w))} | MB: {mb} | Multiplier: {m}")

    # Full history frequency
    white_all, mb_all, mult_all = [], [], []
    for _, _, w, mb, m in draws:
        white_all.extend(w)
        mb_all.append(mb)
        mult_all.append(m)

    white_full = Counter(white_all)
    mb_full = Counter(mb_all)
    mult_full = Counter(mult_all)

    # Last 50 window
    last_n = 50
    last_draws = draws[:last_n]
    white_last, mb_last = [], []
    for _, _, w, mb, _ in last_draws:
        white_last.extend(w)
        mb_last.append(mb)

    white_last_c = Counter(white_last)
    mb_last_c = Counter(mb_last)

    # Thresholds (tunable)
    HOT_MIN_WHITE = 210
    MED_MIN_WHITE = 180
    HOT_MIN_MB = 70
    MED_MIN_MB = 55

    print("\nLATEST DRAW SUMMARY")
    print("-" * 80)
    print(f"{latest_d} | White: {' '.join(map(str, latest_white))} | MB: {latest_mb} | Multiplier: {latest_mult}")

    # Latest draw frequency check
    mix = Counter()

    print("\nLATEST DRAW: FREQUENCY CHECK (WHITE BALLS) [FULL]")
    print("-" * 80)
    for num in latest_white:
        f = white_full.get(num, 0)
        b = classify_bucket(f, HOT_MIN_WHITE, MED_MIN_WHITE)
        mix[b] += 1
        print(f"{num:2d} -> {f} times -> {b}")

    mb_freq = mb_full.get(latest_mb, 0)
    mb_bucket = classify_bucket(mb_freq, HOT_MIN_MB, MED_MIN_MB)

    print("\nLATEST DRAW: FREQUENCY CHECK (MEGA BALL) [FULL]")
    print("-" * 80)
    print(f"{latest_mb:2d} -> {mb_freq} times -> {mb_bucket}")

    print("\nLATEST DRAW MIX LABEL (WHITE BALLS)")
    print("-" * 80)
    print(f"{mix.get('HOT', 0)} HOT | {mix.get('MEDIUM', 0)} MEDIUM | {mix.get('COLD', 0)} COLD")

    # Top lists
    print("\nTOP 10 WHITE BALLS (FULL HISTORY)")
    print("-" * 80)
    for n, c in top_n(white_full, 10):
        print(f"{n:2d} -> {c} times")

    print("\nTOP 10 WHITE BALLS (LAST 50 DRAWS)")
    print("-" * 80)
    for n, c in top_n(white_last_c, 10):
        print(f"{n:2d} -> {c} times")

    print("\nTOP 10 MEGA BALLS (FULL HISTORY)")
    print("-" * 80)
    for n, c in top_n(mb_full, 10):
        print(f"{n:2d} -> {c} times")

    print("\nTOP 10 MEGA BALLS (LAST 50 DRAWS)")
    print("-" * 80)
    for n, c in top_n(mb_last_c, 10):
        print(f"{n:2d} -> {c} times")

    print("\nTOP MULTIPLIERS (FULL HISTORY)")
    print("-" * 80)
    for k, c in mult_full.most_common(5):
        print(f"{k} -> {c} times")

    # ✅ FULL TABLES YOU ASKED FOR
    print("\nWHITE BALL FREQUENCY (1–70) [FULL]")
    print("-" * 80)
    for i in range(1, 71):
        print(f"{i:2d} -> {white_full.get(i, 0)} times")

    print("\nMEGA BALL FREQUENCY (1–25) [FULL]")
    print("-" * 80)
    for i in range(1, 26):
        print(f"{i:2d} -> {mb_full.get(i, 0)} times")


if __name__ == "__main__":
    main()
