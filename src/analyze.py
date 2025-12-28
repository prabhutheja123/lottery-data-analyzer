from collections import Counter
import csv
from datetime import datetime

PB_CSV   = "data/nj/powerball.csv"
MEGA_CSV = "data/nj/mega_millions.csv"

def parse_date(d): 
    return datetime.strptime(d, "%m/%d/%Y")

def read_draws(csv_file, ball_name):
    draws = []
    with open(csv_file, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            white = list(map(int, row["white_numbers"].split()))
            ball  = int(row[ball_name])
            draws.append((row["draw_date"], white, ball))
    return draws

def analyze(title, draws, white_max, ball_max, ball_label):
    print(f"\n===== {title} =====")
    draws = sorted(draws, key=lambda x: parse_date(x[0]), reverse=True)

    print("\nLatest 10 draws")
    print("-" * 40)
    for d, w, b in draws[:10]:
        print(f"{d} | White: {' '.join(map(str,w))} | {ball_label}: {b}")

    white_all, ball_all = [], []
    for _, w, b in draws:
        white_all.extend(w)
        ball_all.append(b)

    print(f"\nWHITE BALL FREQUENCY (1–{white_max})")
    for i in range(1, white_max + 1):
        print(f"{i:2d} -> {Counter(white_all).get(i,0)} times")

    print(f"\n{ball_label.upper()} FREQUENCY (1–{ball_max})")
    for i in range(1, ball_max + 1):
        print(f"{i:2d} -> {Counter(ball_all).get(i,0)} times")

def main():
    analyze(
        "POWERBALL",
        read_draws(PB_CSV, "powerball"),
        69, 26, "PB"
    )

    analyze(
        "MEGA MILLIONS",
        read_draws(MEGA_CSV, "mega_ball"),
        70, 25, "MB"
    )

if __name__ == "__main__":
    main()
