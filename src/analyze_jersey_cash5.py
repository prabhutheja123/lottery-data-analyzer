import os
import sys
import csv
from collections import Counter

sys.path.append("src")
from common import parse_date  # noqa: E402

JC5_CSV = "data/nj/jersey_cash5.csv"


def classify_bucket(freq: int, hot_min: int, med_min: int) -> str:
    if freq >= hot_min:
        return "HOT"
    if freq >= med_min:
        return "MEDIUM"
    return "COLD"


def top_n(counter: Counter, n: int = 10):
    return counter.most_common(n)


def read_draws(path: str):
    draws = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            d = (row.get("draw_date") or "").strip()
            nums = (row.get("numbers") or "").strip()
            xtra = (row.get("xtra") or "N/A").strip()

            if not d or not nums:
                continue

            dt = parse_date(d)
            if dt is None:
                continue

            try:
                balls = list(map(int, nums.split()))
                if len(balls) != 5:
                    continue
            except Exception:
                continue

            draws.append((d, dt, balls, xtra))
    return draws


def main():
    print("\n===== JERSEY CASH 5 =====")
    print("Looking for:", JC5_CSV)
    print("Exists?:", os.path.exists(JC5_CSV))

    if not os.path.exists(JC5_CSV):
        print("❌ ERROR: jersey_cash5.csv not found.")
        print("✅ Fix: Ensure src/fetch_nj_latest.py writes data/nj/jersey_cash5.csv")
        return

    draws = read_draws(JC5_CSV)
    print("Valid draws parsed:", len(draws))

    if not draws:
        print("❌ No valid draws found — check CSV contents.")
        return

    draws.sort(key=lambda x: x[1], reverse=True)

    latest_d, _, latest_nums, latest_xtra = draws[0]

    print("\nLatest 10 draws")
    print("-" * 80)
    for d, _, nums, xtra in draws[:10]:
        print(f"{d} | Numbers: {' '.join(map(str, nums))} | XTRA: {xtra}")

    # frequencies (full)
    all_nums = []
    all_xtra = []
    for _, _, nums, xtra in draws:
        all_nums.extend(nums)
        all_xtra.append(xtra)

    freq_full = Counter(all_nums)
    xtra_full = Counter(all_xtra)

    # last 50
    last_n = 50
    last_draws = draws[:last_n]
    last_nums = []
    for _, _, nums, _ in last_draws:
        last_nums.extend(nums)
    freq_last = Counter(last_nums)

    # thresholds (tune later)
    HOT_MIN = 210
    MED_MIN = 180

    print("\nLATEST DRAW SUMMARY")
    print("-" * 80)
    print(f"{latest_d} | Numbers: {' '.join(map(str, latest_nums))} | XTRA: {latest_xtra}")

    # latest draw frequency check
    mix = Counter()
    print("\nLATEST DRAW: FREQUENCY CHECK (FULL)")
    print("-" * 80)
    for n in latest_nums:
        f = freq_full.get(n, 0)
        b = classify_bucket(f, HOT_MIN, MED_MIN)
        mix[b] += 1
        print(f"{n:2d} -> {f} times -> {b}")

    print("\nLATEST DRAW MIX LABEL")
    print("-" * 80)
    print(f"{mix.get('HOT',0)} HOT | {mix.get('MEDIUM',0)} MEDIUM | {mix.get('COLD',0)} COLD")

    print("\nTOP 10 NUMBERS (FULL HISTORY)")
    print("-" * 80)
    for n, c in top_n(freq_full, 10):
        print(f"{n:2d} -> {c} times")

    print("\nTOP 10 NUMBERS (LAST 50 DRAWS)")
    print("-" * 80)
    for n, c in top_n(freq_last, 10):
        print(f"{n:2d} -> {c} times")

    print("\nXTRA FREQUENCY (FULL HISTORY)")
    print("-" * 80)
    for k, c in xtra_full.most_common():
        print(f"{k} -> {c} times")

    # Full tables like you asked (1–45)
    print("\nNUMBER FREQUENCY (1–45) [FULL]")
    print("-" * 80)
    for i in range(1, 46):
        print(f"{i:2d} -> {freq_full.get(i, 0)} times")


if __name__ == "__main__":
    main()
