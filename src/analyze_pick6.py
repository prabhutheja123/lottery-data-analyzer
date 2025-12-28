import os
from collections import Counter
from common import parse_date, read_csv

PICK6_CSV = "data/nj/pick6.csv"

def main():
    print("\n===== PICK 6 (NJ) =====")
    print("Looking for:", PICK6_CSV)
    print("Exists?:", os.path.exists(PICK6_CSV))

    if not os.path.exists(PICK6_CSV):
        print("❌ ERROR: pick6.csv not found.")
        print("✅ Fix: Ensure src/fetch_nj_latest.py runs and saves to data/nj/pick6.csv")
        return

    rows = read_csv(PICK6_CSV)
    if not rows:
        print("❌ ERROR: pick6.csv exists but has 0 rows.")
        return

    draws = []
    bad = 0

    for r in rows:
        try:
            d = (r.get("draw_date") or "").strip()
            main_str = (r.get("main_numbers") or "").strip()
            dp_str = (r.get("double_play_numbers") or "").strip()

            if not d or not main_str or not dp_str:
                bad += 1
                continue

            main_nums = list(map(int, main_str.split()))
            dp_nums = list(map(int, dp_str.split()))

            if len(main_nums) != 6 or len(dp_nums) != 6:
                bad += 1
                continue

            draws.append((d, main_nums, dp_nums))
        except Exception:
            bad += 1

    print("Total rows read:", len(rows))
    print("Valid draws parsed:", len(draws))
    print("Bad/Skipped rows:", bad)

    if not draws:
        print("❌ ERROR: No valid Pick-6 draws parsed. Check fetch parsing.")
        return

    draws.sort(key=lambda x: parse_date(x[0]), reverse=True)

    print("\nLatest 10 draws")
    print("-" * 60)
    for d, main_nums, dp_nums in draws[:10]:
        print(f"{d} | Main: {' '.join(map(str, main_nums))} | DP: {' '.join(map(str, dp_nums))}")

    # Frequency counts (separate)
    main_all = []
    dp_all = []
    for _, main_nums, dp_nums in draws:
        main_all.extend(main_nums)
        dp_all.extend(dp_nums)

    print("\nMAIN NUMBER FREQUENCY (1–46)")
    print("-" * 40)
    mc = Counter(main_all)
    for i in range(1, 47):
        print(f"{i:2d} -> {mc.get(i, 0)} times")

    print("\nDOUBLE PLAY FREQUENCY (1–46)")
    print("-" * 40)
    dc = Counter(dp_all)
    for i in range(1, 47):
        print(f"{i:2d} -> {dc.get(i, 0)} times")

if __name__ == "__main__":
    main()
