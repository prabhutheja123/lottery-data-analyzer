import os
from collections import Counter
from common import parse_date, read_csv

PB_CSV = "data/nj/powerball.csv"

def main():
    print("\n===== POWERBALL =====")
    print("Looking for:", PB_CSV)
    print("Exists?:", os.path.exists(PB_CSV))

    if not os.path.exists(PB_CSV):
        print("❌ ERROR: powerball.csv not found.")
        print("✅ Fix: Ensure src/fetch_nj_latest.py runs and saves to data/nj/powerball.csv")
        print("Tip: Add a debug step in workflow: ls -R data")
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
            draw_date = r["draw_date"]
            white_str = (r.get("white_numbers") or "").strip()
            pb_str = (r.get("powerball") or "").strip()

            if not draw_date or not white_str or not pb_str:
                bad_rows += 1
                continue

            white = list(map(int, white_str.split()))
            pb = int(pb_str)

            draws.append((draw_date, white, pb))
        except Exception:
            bad_rows += 1

    print("Total rows read:", len(rows))
    print("Valid draws parsed:", len(draws))
    print("Bad/Skipped rows:", bad_rows)

    if not draws:
        print("❌ ERROR: No valid draws parsed.")
        print("✅ Fix: Inspect CSV headers/values in data/nj/powerball.csv")
        return

    draws.sort(key=lambda x: parse_date(x[0]), reverse=True)

    print("\nLatest 10 draws")
    print("-" * 40)
    for d, w, pb in draws[:10]:
        print(f"{d} | White: {' '.join(map(str, w))} | PB: {pb}")

    white_all, pb_all = [], []
    for _, w, pb in draws:
        white_all.extend(w)
        pb_all.append(pb)

    print("\nWHITE BALL FREQUENCY (1–69)")
    print("-" * 40)
    wc = Counter(white_all)
    for i in range(1, 70):
        print(f"{i:2d} -> {wc.get(i, 0)} times")

    print("\nPOWERBALL FREQUENCY (1–26)")
    print("-" * 40)
    pc = Counter(pb_all)
    for i in range(1, 27):
        print(f"{i:2d} -> {pc.get(i, 0)} times")


if __name__ == "__main__":
    main()
