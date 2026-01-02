import os
import sys
import csv
import re
from collections import Counter

sys.path.append("src")
from common import parse_date  # noqa: E402

MEGA_CSV = "data/nj/mega_millions.csv"

LATEST_N = 20
LAST_N_FOR_TOP = 50


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


# ------------------ 6-level buckets ------------------
def classify_white_6(freq: int) -> str:
    # Uses the same FULL-history ranges you validated earlier.
    if freq >= 225:
        return "VERY HOT"
    if 210 <= freq <= 224:
        return "HOT"
    if 195 <= freq <= 209:
        return "MEDIUM"
    if 180 <= freq <= 194:
        return "LESS MEDIUM"
    if 150 <= freq <= 179:
        return "LOW"
    return "VERY LOW"


def classify_mb_6(freq: int, max_freq: int) -> str:
    """
    Mega ball frequencies are much smaller (1–25),
    so we classify relative to FULL-history max frequency.
    """
    if max_freq <= 0:
        return "VERY LOW"

    if freq >= 0.85 * max_freq:
        return "VERY HOT"
    if freq >= 0.70 * max_freq:
        return "HOT"
    if freq >= 0.55 * max_freq:
        return "MEDIUM"
    if freq >= 0.40 * max_freq:
        return "LESS MEDIUM"
    if freq >= 0.25 * max_freq:
        return "LOW"
    return "VERY LOW"


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

    # Show latest 20 draws (was 10)
    print(f"\nLatest {LATEST_N} draws")
    print("-" * 80)
    for d, _, w, mb, m in draws[:LATEST_N]:
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

    mb_full_max = max(mb_full.values()) if mb_full else 0

    # Last 50 window (unchanged)
    last_draws = draws[:LAST_N_FOR_TOP]
    white_last, mb_last = [], []
    for _, _, w, mb, _ in last_draws:
        white_last.extend(w)
        mb_last.append(mb)

    white_last_c = Counter(white_last)
    mb_last_c = Counter(mb_last)

    # ---- New: For EACH of the latest 20 draws, show FULL-history counts + 6 labels ----
    print(f"\nLAST {LATEST_N} DRAWS: FREQUENCY CHECK (WHITE BALLS) [FULL]")
    print("-" * 80)

    for d, _, w, mb, m in draws[:LATEST_N]:
        print(f"{d} | White: {' '.join(map(str, w))} | MB: {mb} | Multiplier: {m}")

        mix6 = Counter()
        for num in w:
            f = white_full.get(num, 0)  # FULL history
            b = classify_white_6(f)
            mix6[b] += 1
            print(f"{num:2d} -> {f} times -> {b}")

        print("\nMIX LABEL (WHITE BALLS)")
        print(f"{mix6.get('VERY HOT', 0)} VERY HOT | "
              f"{mix6.get('HOT', 0)} HOT | "
              f"{mix6.get('MEDIUM', 0)} MEDIUM | "
              f"{mix6.get('LESS MEDIUM', 0)} LESS MEDIUM | "
              f"{mix6.get('LOW', 0)} LOW | "
              f"{mix6.get('VERY LOW', 0)} VERY LOW")
        print("-" * 35)

    print(f"\nLAST {LATEST_N} DRAWS: FREQUENCY CHECK (MEGA BALL) [FULL]")
    print("-" * 80)

    for d, _, w, mb, m in draws[:LATEST_N]:
        mb_freq = mb_full.get(mb, 0)  # FULL history
        mb_bucket = classify_mb_6(mb_freq, mb_full_max)
        print(f"{d} | MB: {mb} | Multiplier: {m}")
        print(f"{mb:2d} -> {mb_freq} times -> {mb_bucket}")
        print("-" * 35)

    # ---- Top lists (unchanged) ----
    print("\nTOP 10 WHITE BALLS (FULL HISTORY)")
    print("-" * 80)
    for n, c in top_n(white_full, 10):
        print(f"{n:2d} -> {c} times")

    print(f"\nTOP 10 WHITE BALLS (LAST {LAST_N_FOR_TOP} DRAWS)")
    print("-" * 80)
    for n, c in top_n(white_last_c, 10):
        print(f"{n:2d} -> {c} times")

    print("\nTOP 10 MEGA BALLS (FULL HISTORY)")
    print("-" * 80)
    for n, c in top_n(mb_full, 10):
        print(f"{n:2d} -> {c} times")

    print(f"\nTOP 10 MEGA BALLS (LAST {LAST_N_FOR_TOP} DRAWS)")
    print("-" * 80)
    for n, c in top_n(mb_last_c, 10):
        print(f"{n:2d} -> {c} times")

    print("\nTOP MULTIPLIERS (FULL HISTORY)")
    print("-" * 80)
    for k, c in mult_full.most_common(5):
        print(f"{k} -> {c} times")

    # ---- FULL tables (unchanged) ----
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
