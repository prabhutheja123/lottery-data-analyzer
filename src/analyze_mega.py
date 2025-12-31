import os
import sys
import csv
import re
import json
from datetime import datetime
from collections import Counter

# CI-friendly charts
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.append("src")
from common import parse_date  # noqa: E402

MEGA_CSV = "data/nj/mega_millions.csv"

OUT_DIR = "reports/nj/mega_millions"
os.makedirs(OUT_DIR, exist_ok=True)


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

            # parse_date can return None if format is bad; keep it, but we’ll handle later
            dt = parse_date(d)
            draws.append((d, dt, white, mega_ball, mult))

    return draws


def classify_bucket(freq: int, hot_min: int, med_min: int) -> str:
    if freq >= hot_min:
        return "HOT"
    if freq >= med_min:
        return "MEDIUM"
    return "COLD"


def write_csv(path: str, rows: list, fieldnames: list):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def write_json(path: str, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def plot_bar(x, y, title: str, xlabel: str, ylabel: str, out_path: str, top_n: int = None):
    if top_n is not None:
        x = x[:top_n]
        y = y[:top_n]

    plt.figure()
    plt.bar(x, y)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def main():
    print("\n===== MEGA MILLIONS =====")
    print("Looking for:", MEGA_CSV)
    print("Exists?:", os.path.exists(MEGA_CSV))

    if not os.path.exists(MEGA_CSV):
        print("❌ ERROR: mega_millions.csv not found.")
        print("✅ Fix: Ensure src/fetch_nj_latest.py runs and saves to data/nj/mega_millions.csv")
        return

    draws = read_mega_draws(MEGA_CSV)
    print(f"Total draws loaded (raw): {len(draws)}")

    if not draws:
        print("❌ No data found — check CSV generation (headers/values).")
        return

    # Drop rows with invalid dates to avoid sort crash
    valid_draws = [d for d in draws if d[1] is not None]
    dropped = len(draws) - len(valid_draws)
    if dropped:
        print(f"⚠️ Dropped {dropped} rows due to invalid draw_date format.")

    if not valid_draws:
        print("❌ All rows had invalid dates. Check draw_date values in CSV.")
        return

    # Sort by parsed datetime (dt) desc
    valid_draws.sort(key=lambda x: x[1], reverse=True)

    # Latest draw
    latest_d, latest_dt, latest_white, latest_mb, latest_mult = valid_draws[0]

    print("\nLatest 10 draws")
    print("-" * 80)
    for d, _, w, mb, m in valid_draws[:10]:
        print(f"{d} | White: {' '.join(map(str, w))} | MB: {mb} | Multiplier: {m}")

    # Build frequencies (full history)
    white_all, mega_all, mult_all = [], [], []
    for _, _, w, mb, m in valid_draws:
        white_all.extend(w)
        mega_all.append(mb)
        mult_all.append(m)

    white_freq_all = Counter(white_all)
    mega_freq_all = Counter(mega_all)
    mult_freq_all = Counter(mult_all)

    # Console: full frequencies
    print("\nWHITE BALL FREQUENCY (1–70) [FULL HISTORY]")
    print("-" * 50)
    for i in range(1, 71):
        print(f"{i:2d} -> {white_freq_all.get(i, 0)} times")

    print("\nMEGA BALL FREQUENCY (1–25) [FULL HISTORY]")
    print("-" * 50)
    for i in range(1, 26):
        print(f"{i:2d} -> {mega_freq_all.get(i, 0)} times")

    print("\nMULTIPLIER FREQUENCY [FULL HISTORY]")
    print("-" * 50)
    for k in sorted(mult_freq_all.keys()):
        print(f"{k} -> {mult_freq_all[k]} times")

    # Rolling window: last 50 draws
    last_n = 50
    last_draws = valid_draws[:last_n]
    white_last, mega_last = [], []
    for _, _, w, mb, _ in last_draws:
        white_last.extend(w)
        mega_last.append(mb)

    white_freq_last = Counter(white_last)
    mega_freq_last = Counter(mega_last)

    # Buckets (you can adjust later)
    HOT_MIN_WHITE = 210
    MED_MIN_WHITE = 180

    # MegaBall counts are usually smaller; these are reasonable defaults
    HOT_MIN_MB = 70
    MED_MIN_MB = 55

    # Latest draw checks
    latest_rows = []
    mix = Counter()

    for num in latest_white:
        f_all = white_freq_all.get(num, 0)
        bucket = classify_bucket(f_all, HOT_MIN_WHITE, MED_MIN_WHITE)
        mix[bucket] += 1
        latest_rows.append(
            {
                "draw_date": latest_d,
                "number": num,
                "frequency_full_history": f_all,
                "bucket": bucket,
            }
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
    """
    Reads Mega Millions CSV with columns:
      - draw_date
      - white_numbers (5 ints space-separated)
      - mega_ball
      - multiplier
    """
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


if __name__ == "__main__":
    main()
