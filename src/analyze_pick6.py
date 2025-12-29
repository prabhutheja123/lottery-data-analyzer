import os
import re
from collections import Counter
from pathlib import Path

from common import parse_date, read_csv

PICK6_CSV = Path("data/nj/pick6.csv")
REPORTS_DIR = Path("reports")


def parse_numbers(s: str) -> list[int]:
    """
    Parses numbers from a string that may contain spaces/commas/dashes/pipes.
    Examples:
      "1 2 3 4 5 6"
      "1,2,3,4,5,6"
      "1-2-3-4-5-6"
      "1 | 2 | 3 | 4 | 5 | 6"
    """
    if not s:
        return []
    parts = re.findall(r"\d+", s)
    return [int(x) for x in parts]


def in_range(nums: list[int], lo: int, hi: int) -> bool:
    return all(lo <= n <= hi for n in nums)


def write_frequency_csv(path: Path, counter: Counter, lo: int, hi: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("number,count\n")
        for n in range(lo, hi + 1):
            f.write(f"{n},{counter.get(n, 0)}\n")


def main(top_n: int = 15) -> None:
    print("\n===== PICK 6 (NJ) =====")
    print("Looking for:", str(PICK6_CSV))
    print("Exists?:", PICK6_CSV.exists())

    if not PICK6_CSV.exists():
        print("❌ ERROR: pick6.csv not found.")
        print("✅ Fix: Ensure src/fetch_nj_latest.py runs and saves to data/nj/pick6.csv")
        return

    rows = read_csv(str(PICK6_CSV))
    if not rows:
        print("❌ ERROR: pick6.csv exists but has 0 rows.")
        return

    draws: list[tuple[str, list[int], list[int]]] = []
    bad = 0

    for r in rows:
        try:
            d = (r.get("draw_date") or "").strip()
            main_str = (r.get("main_numbers") or "").strip()
            dp_str = (r.get("double_play_numbers") or "").strip()

            if not d or not main_str or not dp_str:
                bad += 1
                continue

            main_nums = parse_numbers(main_str)
            dp_nums = parse_numbers(dp_str)

            # Pick-6 should be exactly 6 numbers each
            if len(main_nums) != 6 or len(dp_nums) != 6:
                bad += 1
                continue

            # NJ Pick-6 is 1–46 (based on your print range)
            if not in_range(main_nums, 1, 46) or not in_range(dp_nums, 1, 46):
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
    main_all: list[int] = []
    dp_all: list[int] = []
    for _, main_nums, dp_nums in draws:
        main_all.extend(main_nums)
        dp_all.extend(dp_nums)

    mc = Counter(main_all)
    dc = Counter(dp_all)

    print("\nTOP MAIN NUMBERS")
    print("-" * 40)
    for n, c in mc.most_common(top_n):
        print(f"{n:2d} -> {c} times")

    print("\nTOP DOUBLE PLAY NUMBERS")
    print("-" * 40)
    for n, c in dc.most_common(top_n):
        print(f"{n:2d} -> {c} times")

    # Full distribution (1–46) to CSV reports
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    write_frequency_csv(REPORTS_DIR / "pick6_main_frequency.csv", mc, 1, 46)
    write_frequency_csv(REPORTS_DIR / "pick6_double_play_frequency.csv", dc, 1, 46)

    print("\n✅ Saved reports:")
    print(" -", REPORTS_DIR / "pick6_main_frequency.csv")
    print(" -", REPORTS_DIR / "pick6_double_play_frequency.csv")


if __name__ == "__main__":
    main()
