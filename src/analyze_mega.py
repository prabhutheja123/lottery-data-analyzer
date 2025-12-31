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
        )

    latest_mb_freq = mega_freq_all.get(latest_mb, 0)
    latest_mb_bucket = classify_bucket(latest_mb_freq, HOT_MIN_MB, MED_MIN_MB)

    mix_label = f"{mix.get('HOT',0)}_HOT__{mix.get('MEDIUM',0)}_MEDIUM__{mix.get('COLD',0)}_COLD"

    print("\nLATEST DRAW: FREQUENCY CHECK (WHITE BALLS)")
    print("-" * 80)
    for r in latest_rows:
        print(f"{r['number']:2d} -> {r['frequency_full_history']} times -> {r['bucket']}")

    print("\nLATEST DRAW: FREQUENCY CHECK (MEGA BALL)")
    print("-" * 80)
    print(f"{latest_mb:2d} -> {latest_mb_freq} times -> {latest_mb_bucket}")

    print("\nLATEST DRAW MIX LABEL")
    print("-" * 80)
    print(f"{latest_d} | White: {' '.join(map(str, latest_white))} | MB: {latest_mb} | {mix_label}")

    # Save outputs
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    latest_csv = os.path.join(OUT_DIR, f"latest_draw_frequency_{run_id}.csv")
    latest_json = os.path.join(OUT_DIR, f"latest_draw_frequency_{run_id}.json")
    compare_csv = os.path.join(OUT_DIR, f"white_compare_last50_vs_full_{run_id}.csv")

    write_csv(
        latest_csv,
        latest_rows,
        ["draw_date", "number", "frequency_full_history", "bucket"],
    )

    payload = {
        "run_id": run_id,
        "total_draws_loaded": len(valid_draws),
        "latest_draw": {
            "draw_date": latest_d,
            "white_numbers": latest_white,
            "mega_ball": latest_mb,
            "multiplier": latest_mult,
            "draw_mix_label": mix_label,
            "white_ball_checks": latest_rows,
            "mega_ball_check": {
                "number": latest_mb,
                "frequency_full_history": latest_mb_freq,
                "bucket": latest_mb_bucket,
            },
        },
        "thresholds": {
            "white": {"HOT_MIN": HOT_MIN_WHITE, "MED_MIN": MED_MIN_WHITE},
            "mega_ball": {"HOT_MIN": HOT_MIN_MB, "MED_MIN": MED_MIN_MB},
        },
        "notes": "Descriptive analysis only (not prediction).",
    }
    write_json(latest_json, payload)

    # Compare last 50 vs full (white balls 1–70)
    compare_rows = []
    for i in range(1, 71):
        compare_rows.append(
            {
                "number": i,
                "freq_full_history": white_freq_all.get(i, 0),
                "freq_last_50_draws": white_freq_last.get(i, 0),
                "delta_last50_minus_full": white_freq_last.get(i, 0) - white_freq_all.get(i, 0),
            }
        )
    write_csv(
        compare_csv,
        compare_rows,
        ["number", "freq_full_history", "freq_last_50_draws", "delta_last50_minus_full"],
    )

    # Charts
    white_sorted = sorted(white_freq_all.items(), key=lambda kv: kv[1], reverse=True)
    x_white = [str(k) for k, _ in white_sorted]
    y_white = [v for _, v in white_sorted]
    chart_white_top20 = os.path.join(OUT_DIR, f"chart_white_top20_full_{run_id}.png")
    plot_bar(
        x_white,
        y_white,
        "Mega Millions White Balls - Top 20 Frequency (Full History)",
        "Number",
        "Count",
        chart_white_top20,
        top_n=20,
    )

    x_mb = [str(i) for i in range(1, 26)]
    y_mb = [mega_freq_all.get(i, 0) for i in range(1, 26)]
    chart_mb = os.path.join(OUT_DIR, f"chart_mega_ball_full_{run_id}.png")
    plot_bar(
        x_mb,
        y_mb,
        "Mega Millions Mega Ball Frequency (Full History)",
        "Mega Ball",
        "Count",
        chart_mb,
        top_n=None,
    )

    white_last_sorted = sorted(white_freq_last.items(), key=lambda kv: kv[1], reverse=True)
    x_white_last = [str(k) for k, _ in white_last_sorted]
    y_white_last = [v for _, v in white_last_sorted]
    chart_white_last20 = os.path.join(OUT_DIR, f"chart_white_top20_last50_{run_id}.png")
    plot_bar(
        x_white_last,
        y_white_last,
        "Mega Millions White Balls - Top 20 Frequency (Last 50 Draws)",
        "Number",
        "Count",
        chart_white_last20,
        top_n=20,
    )

    summary_json = os.path.join(OUT_DIR, f"summary_{run_id}.json")
    summary = {
        "run_id": run_id,
        "total_draws_loaded": len(valid_draws),
        "latest_draw_date": latest_d,
        "latest_draw_white_numbers": latest_white,
        "latest_draw_mega_ball": latest_mb,
        "latest_draw_mix_label": mix_label,
        "files": {
            "latest_draw_csv": latest_csv,
            "latest_draw_json": latest_json,
            "compare_csv": compare_csv,
            "chart_white_top20_full": chart_white_top20,
            "chart_mega_ball_full": chart_mb,
            "chart_white_top20_last50": chart_white_last20,
        },
    }
    write_json(summary_json, summary)

    print("\n✅ Reports saved to:", OUT_DIR)
    print(" -", latest_csv)
    print(" -", latest_json)
    print(" -", compare_csv)
    print(" -", chart_white_top20)
    print(" -", chart_mb)
    print(" -", chart_white_last20)
    print(" -", summary_json)


if __name__ == "__main__":
    main()
