from collections import Counter
import csv
from datetime import datetime

INPUT_CSV = "data/nj/powerball.csv"

def parse_draw_date(date_str: str) -> datetime:
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            pass
    raise ValueError(f"Unsupported date format: {date_str}")

def read_draws(csv_path):
    draws = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            draw_date = row["draw_date"].strip()
            white = [int(x) for x in row["white_numbers"].split()]
            pb = int(row["powerball"])
            draws.append((draw_date, white, pb))
    return draws

def main():
    draws = read_draws(INPUT_CSV)

    print(f"Analyzing file: {INPUT_CSV}")
    print(f"Total draws loaded: {len(draws)}")
    print()

    # ===== Latest 10 draws (correctly sorted) =====
    draws_sorted = sorted(draws, key=lambda x: parse_draw_date(x[0]), reverse=True)
    latest_10 = draws_sorted[:10]

    print("Latest 10 winning draws")
    print("-" * 40)
    for draw_date, white, pb in latest_10:
        print(f"{draw_date} | White: {' '.join(map(str, white))} | PB: {pb}")
    print()

    # ===== Collect numbers =====
    white_all = []
    pb_all = []

    for _, white, pb in draws:
        white_all.extend(white)
        pb_all.append(pb)

    white_freq = Counter(white_all)
    pb_freq = Counter(pb_all)

    # ===== FULL WHITE BALL DISTRIBUTION =====
    print("WHITE BALL FREQUENCY (1–69)")
    print("-" * 40)
    for num in range(1, 70):
        print(f"{num:2d} -> {white_freq.get(num, 0)} times")
    print()

    # ===== FULL POWERBALL DISTRIBUTION =====
    print("POWERBALL FREQUENCY (1–26)")
    print("-" * 40)
    for num in range(1, 27):
        print(f"{num:2d} -> {pb_freq.get(num, 0)} times")

if __name__ == "__main__":
    main()
