import os
import sys
from collections import Counter

sys.path.append("src")
from common import parse_date, read_csv  # noqa: E402

PB_CSV = "data/nj/powerball.csv"


def classify_bucket(freq: int, hot_min: int, med_min: int) -> str:
    if freq >= hot_min:
        return "HOT"
    if freq >= med_min:
        return "MEDIUM"
    return "COLD"


def top_n(counter: Counter, n: int = 10):
    return counter.most_common(n)


def main():
    print("\n===== POWERBALL =====")
    print("Looking for:", PB_CSV)
    print("Exists?:", os.path.exists(PB_CSV))

    if not os.path.exists(PB_CSV):
        print("❌ ERROR: powerball.csv not found.")
        print("✅ Fix: Ensure src/fetch_nj_latest.py runs and saves to data/nj/powerball.csv")
        return

    rows = read_csv(PB_CSV)

    if not rows:
        print("❌ ERROR: powerball.csv exists but has 0 rows (only header or empty file).")
        print("✅ Fix: Check fetch_nj_latest.py parsing and row-writing logic.")
        return

    draws = []
    bad_rows = 0

    for r in rows:
        try:
            draw_date = (r.get("draw_date") or "").strip()
            white_str = (r.get("white_numbers") or "").strip()
            pb_str = (r.get("powerball") or "").strip()

            if not draw_date or not white_str or not pb_str:
                bad_rows += 1
                continue

            dt = parse_date(draw_date)  # can be None if bad format (with our updated common.py)
            if dt is None:
                bad_rows += 1
                continue

            white = list(map(int, white_str.split()))
            pb = int(pb_str)

            # Powerball has 5 white balls
            if len(white) != 5:
                bad_rows += 1
                continue

            draws.append((draw_date, dt, white, pb))
        except Exception:
            bad_rows += 1

    print("Total rows read:", len(rows))
    print("Valid draws parsed:", len(draws))
    print("Bad/Skipped rows:", bad_rows)

    if not draws:
        print("❌ ERROR: No valid draws parsed.")
        print("✅ Fix: Inspect CSV headers/values in data/nj/powerball.csv")
        return

    # Sort by parsed datetime
    draws.sort(key=lambda x: x[1], reverse=True)

    # Latest draw
    latest_date, _, latest_white, latest_pb = draws[0]

    print("\nLatest 10 draws")
    print("-" * 60)
    for d, _, w, pb in draws[:10]:
        print(f"{d} | White: {' '.join(map(str, w))} | PB: {pb}")

    # Build full-history frequency
    white_all, pb_all = [], []
    for _, _, w, pb in draws:
        white_all.extend(w)
        pb_all.append(pb)

    white_full = Counter(white_all)
    pb_full = Counter(pb_all)

    # Rolling window (last 50 draws)
    last_n = 50
    last_draws = draws[:last_n]
    white_last, pb_last = [], []
    for _, _, w, pb in last_draws:
        white_last.extend(w)
        pb_last.append(pb)

    white_last_c = Counter(white_last)
    pb_last_c = Counter(pb_last)

    # ---- Buckets (thresholds) ----
    # White balls range 1–69, counts depend on dataset size.
    # These are simple defaults; we can tune later if needed.
    HOT_MIN_WHITE = 210
    MED_MIN_WHITE = 180

    # Powerball 1–26 appears less frequently; lower thresholds.
    HOT_MIN_PB = 70
    MED_MIN_PB = 55

    # ---- Latest draw frequency check (FULL history) ----
    mix = Counter()

    print("\nLATEST DRAW SUMMARY")
    print("-" * 60)
    print(f"{latest_date} | White: {' '.join(map(str, latest_white))} | PB: {latest_pb}")

    print("\nLATEST DRAW: FREQUENCY CHECK (WHITE BALLS) [FULL]")
    print("-" * 60)
    for num in latest_white:
        f = white_full.get(num, 0)
        b = classify_bucket(f, HOT_MIN_WHITE, MED_MIN_WHITE)
        mix[b] += 1
        print(f"{num:2d} -> {f} times -> {b}")

    pb_freq = pb_full.get(latest_pb, 0)
    pb_bucket = classify_bucket(pb_freq, HOT_MIN_PB, MED_MIN_PB)

    print("\nLATEST DRAW: FREQUENCY CHECK (POWERBALL) [FULL]")
    print("-" * 60)
    print(f"{latest_pb:2d} -> {pb_freq} times -> {pb_bucket}")

    print("\nLATEST DRAW MIX LABEL (WHITE BALLS)")
    print("-" * 60)
    print(f"{mix.get('HOT', 0)} HOT | {mix.get('MEDIUM', 0)} MEDIUM | {mix.get('COLD', 0)} COLD")

    # ---- Top lists (Full vs Last 50) ----
    print("\nTOP 10 WHITE BALLS (FULL HISTORY)")
    print("-" * 60)
    for n, c in top_n(white_full, 10):
        print(f"{n:2d} -> {c} times")

    print("\nTOP 10 WHITE BALLS (LAST 50 DRAWS)")
    print("-" * 60)
    for n, c in top_n(white_last_c, 10):
        print(f"{n:2d} -> {c} times")

    print("\nTOP 10 POWERBALL NUMBERS (FULL HISTORY)")
    print("-" * 60)
    for n, c in top_n(pb_full, 10):
        print(f"{n:2d} -> {c} times")

    print("\nTOP 10 POWERBALL NUMBERS (LAST 50 DRAWS)")
    print("-" * 60)
    for n, c in top_n(pb_last_c, 10):
        print(f"{n:2d} -> {c} times")

    # Optional: keep your full distribution prints (comment out if too long)
    print("\nWHITE BALL FREQUENCY (1–69) [FULL]")
    print("-" * 60)
    for i in range(1, 70):
        print(f"{i:2d} -> {white_full.get(i, 0)} times")

    print("\nPOWERBALL FREQUENCY (1–26) [FULL]")
    print("-" * 60)
    for i in range(1, 27):
        print(f"{i:2d} -> {pb_full.get(i, 0)} times")


if __name__ == "__main__":
    main()
