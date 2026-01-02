import os
import sys
from collections import Counter

sys.path.append("src")
from common import parse_date, read_csv  # noqa: E402

PB_CSV = "data/nj/powerball.csv"

LATEST_N = 20
LAST_N_FOR_TOP = 50


# ------------------ 6-level buckets ------------------
# White balls use your FULL frequency-based ranges (1–69).
def classify_white_6(freq: int) -> str:
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


# Powerball (1–26) has smaller counts, so we classify relative to max freq in FULL history.
def classify_pb_6(freq: int, max_freq: int) -> str:
    if max_freq <= 0:
        return "VERY LOW"

    # relative bands (tuned for small ranges like 1–26)
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

            dt = parse_date(draw_date)
            if dt is None:
                bad_rows += 1
                continue

            white = list(map(int, white_str.split()))
            pb = int(pb_str)

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

    # Sort newest first
    draws.sort(key=lambda x: x[1], reverse=True)

    # Show latest 20 draws (was 10)
    print(f"\nLatest {LATEST_N} draws")
    print("-" * 60)
    for d, _, w, pb in draws[:LATEST_N]:
        print(f"{d} | White: {' '.join(map(str, w))} | PB: {pb} | Multiplier: N/A")

    # Build FULL-history frequency
    white_all, pb_all = [], []
    for _, _, w, pb in draws:
        white_all.extend(w)
        pb_all.append(pb)

    white_full = Counter(white_all)
    pb_full = Counter(pb_all)
    pb_full_max = max(pb_full.values()) if pb_full else 0

    # Rolling window (last 50 draws) — unchanged
    last_draws = draws[:LAST_N_FOR_TOP]
    white_last, pb_last = [], []
    for _, _, w, pb in last_draws:
        white_last.extend(w)
        pb_last.append(pb)

    white_last_c = Counter(white_last)
    pb_last_c = Counter(pb_last)

    # ---- New: frequency check for EACH of the latest 20 draws (FULL counts) ----
    print(f"\nLAST {LATEST_N} DRAWS: FREQUENCY CHECK (WHITE BALLS) [FULL]")
    print("-" * 60)

    for d, _, w, pb in draws[:LATEST_N]:
        print(f"{d} | White: {' '.join(map(str, w))} | PB: {pb} | Multiplier: N/A")

        mix6 = Counter()
        for num in w:
            f = white_full.get(num, 0)  # FULL history count
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

    print(f"\nLAST {LATEST_N} DRAWS: FREQUENCY CHECK (POWERBALL) [FULL]")
    print("-" * 60)

    for d, _, w, pb in draws[:LATEST_N]:
        pb_freq = pb_full.get(pb, 0)  # FULL history count
        pb_bucket = classify_pb_6(pb_freq, pb_full_max)
        print(f"{d} | PB: {pb} | Multiplier: N/A")
        print(f"{pb:2d} -> {pb_freq} times -> {pb_bucket}")
        print("-" * 35)

    # ---- Top lists (Full vs Last 50) — unchanged ----
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

    # ---- Full distributions — unchanged ----
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
