import csv
from collections import Counter
from datetime import datetime

MEGA_CSV = "data/nj/mega_millions.csv"

def parse_date(d):
    return datetime.strptime(d, "%m/%d/%Y")

def read_mega_draws(csv_file):
    draws = []

    with open(csv_file, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            # SAFETY: skip broken rows
            if not row["white_numbers"]:
                continue

            white = list(map(int, row["white_numbers"].split()))
            mega_ball = int(row["mega_ball"])
            multiplier = row.get("multiplier", "N/A")

            draws.append((
                row["draw_date"],
                white,
                mega_ball,
                multiplier
            ))

    return draws


def main():
    draws = read_mega_draws(MEGA_CSV)

    print("\n===== MEGA MILLIONS =====")
    print(f"Total draws loaded: {len(draws)}")

    # Sort newest first
    draws.sort(key=lambda x: parse_date(x[0]), reverse=True)

    print("\nLatest 10 draws")
    print("-" * 50)
    for d, w, mb, m in draws[:10]:
        print(f"{d} | White: {' '.join(map(str, w))} | MB: {mb} | Multiplier: {m}")

    # Frequency analysis
    white_all = []
    mega_all = []
    multiplier_all = []

    for _, w, mb, m in draws:
        white_all.extend(w)
        mega_all.append(mb)
        if m != "N/A":
            multiplier_all.append(m)

    white_freq = Counter(white_all)
    mega_freq = Counter(mega_all)
    mult_freq = Counter(multiplier_all)

    print("\nWHITE BALL FREQUENCY (1–70)")
    print("-" * 30)
    for i in range(1, 71):
        print(f"{i:2d} -> {white_freq.get(i, 0)} times")

    print("\nMEGA BALL FREQUENCY (1–25)")
    print("-" * 30)
    for i in range(1, 26):
        print(f"{i:2d} -> {mega_freq.get(i, 0)} times")

    print("\nMULTIPLIER FREQUENCY")
    print("-" * 30)
    for k, v in sorted(mult_freq.items()):
        print(f"{k} -> {v} times")


if __name__ == "__main__":
    main()
