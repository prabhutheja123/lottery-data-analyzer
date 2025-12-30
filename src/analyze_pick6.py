import re
from collections import Counter
from pathlib import Path

from common import parse_date, read_csv

PICK6_CSV = Path("data/nj/pick6.csv")
REPORTS_DIR = Path("reports")


def parse_numbers(s: str) -> list[int]:
    return [int(x) for x in re.findall(r"\d+", s or "")]


def in_range(nums: list[int], lo: int, hi: int) -> bool:
    return all(lo <= n <= hi for n in nums)


def write_frequency_csv(path: Path, counter: Counter, lo: int, hi: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("number,count\n")
        for n in range(lo, hi + 1):
            f.write(f"{n},{counter.get(n, 0)}\n")


def print_freq_table(title: str, counter: Counter, lo: int, hi: int) -> None:
    print(f"\n{title} ({lo}–{hi})")
    print("-" * 60)
    for n in range(lo, hi + 1):
        print(f"{n:2d} -> {counter.get(n, 0)} times")


def main(top_n: int = 10) -> None:
    print("\n===== PICK 6 (NJ) =====")
    print("Looking for:", str(PICK6_CSV))
    print("Exists?:", PICK6_CSV.exists())

    if not PICK6_CSV.exists():
        print("⚠️ pick6.csv not found. Skipping Pick 6 analysis.")
        return

    rows = read_csv(str(PICK6_CSV))
    if not rows:
        print("⚠️ Warning: CSV exists but has no data rows ->", str(PICK6_CSV))
        print("⚠️ pick6.csv exists but has 0 rows (likely blocked in CI).")
        print("⚠️ Skipping Pick 6 analysis gracefully.")
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

            main_nums = parse_numbers(main_str)
            dp_nums = parse_numbers(dp_str)

            if len(main_nums) != 6 or len(dp_nums) != 6:
                bad += 1
                continue

            # Pick-6 expected range: 1–46 (adjust if needed)
            if not in_range(main_nums, 1, 46) or not in_range(dp_nums, 1, 46):
                bad += 1
                continue

            draws.append((d, main_nums, dp_nums))
        except Exception:
            bad += 1

    if not draws:
        print("⚠️ No valid Pick-6 draws parsed. Skipping analysis.")
        return

    draws.sort(key=lambda x: parse_date(x[0]), reverse=True)

    # Mega-style latest section
    print("\nLATEST DRAWS")
    print("-" * 60)
    for d, main_nums, dp_nums in draws[:top_n]:
        main_fmt = " ".join(map(str, main_nums))
        dp_fmt = " ".join(map(str, dp_nums))
        print(f"{d} | Main: {main_fmt} | DP: {dp_fmt}")

    # Frequency
    main_all = []
    dp_all = []
    for _, main_nums, dp_nums in draws:
        main_all.extend(main_nums)
        dp_all.extend(dp_nums)

    mc = Counter(main_all)
    dc = Counter(dp_all)

    print_freq_table("MAIN BALL FREQUENCY", mc, 1, 46)
    print_freq_table("DOUBLE PLAY FREQUENCY", dc, 1, 46)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    write_frequency_csv(REPORTS_DIR / "pick6_main_frequency.csv", mc, 1, 46)
    write_frequency_csv(REPORTS_DIR / "pick6_double_play_frequency.csv", dc, 1, 46)

    print("\n✅ Saved reports:")
    print(" -", REPORTS_DIR / "pick6_main_frequency.csv")
    print(" -", REPORTS_DIR / "pick6_double_play_frequency.csv")


if __name__ == "__main__":
    main()
