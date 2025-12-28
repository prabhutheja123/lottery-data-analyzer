import csv
from collections import Counter
from datetime import datetime

MEGA_CSV = "data/nj/mega_millions.csv"


def parse_date(d):
    return datetime.strptime(d, "%Y-%m-%d")


def read_mega_draws(csv_file):
    draws = []

    with open(csv_file, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if not row["white_numbers"]:
                continue

            white = list(map(int, row["white_numbers"].split()))
            mega_ball = int(row["mega_ball"])
            multiplier = row["multiplier"]

            draws.append((row["draw_date"], white, mega_ball, multiplier))

    return draws


def main():
    draws = read_mega_draws(MEGA_CSV)

    print("\n===== MEGA MILLIONS =====")
    print(f"Total draws loaded: {len(draws)}")

    if not draws:
        print("❌ No data found — check CSV generation")
        return

    draws.sort(key=lambda x: parse_date(x[0]), reverse=True)

    print("\nLatest 10 draws")
    print("-" * 50)
    for d, w, mb, m in draws[:10]:
        print(f"{d} | White: {' '.join(map(str, w))} | MB: {mb} | Multiplier: {m}")

    white_all, mega_all, mult_all = [], [], []

    for _, w, mb, m in draws:
        white_all.extend(w)
        mega_all.append(mb)
        mult_all.append(m)

    print("\nWHITE BALL FREQUENCY (1–70)")
    print("-" * 40)
    white_freq = Counter(white_all)
    for i in range(1, 71):
        print(f"{i:2d} -> {white_freq.get(i, 0)} times")

    print("\nMEGA BALL FREQUENCY (1–25)")
    print("-" * 40)
    mega_freq = Counter(mega_all)
    for i in range(1, 26):
        print(f"{i:2d} -> {mega_freq.get(i, 0)} times")

    print("\nMULTIPLIER FREQUENCY")
    print("-" * 40)
    for k, v in Counter(mult_all).items():
        print(f"{k} -> {v} times")


if __name__ == "__main__":
    main()
