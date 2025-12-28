from collections import Counter
import csv

INPUT_CSV = "data/nj/powerball.csv"   # created by fetch script

def read_draws(csv_path):
    draws = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            draw_date = row["draw_date"]
            white = [int(x) for x in row["white_numbers"].split()]
            pb = int(row["powerball"])
            draws.append((draw_date, white, pb))
    return draws

def main():
    draws = read_draws(INPUT_CSV)

    print(f"Analyzing file: {INPUT_CSV}")
    print(f"Total draws loaded: {len(draws)}")
    print()

    # Latest 10 winning numbers (most recent first)
    draws_sorted = sorted(draws, key=lambda x: x[0], reverse=True)
    latest_10 = draws_sorted[:10]

    print("Latest 10 winning draws")
    print("-" * 35)
    for draw_date, white, pb in latest_10:
        white_str = " ".join(map(str, white))
        print(f"{draw_date} | White: {white_str} | PB: {pb}")
    print()

    # Frequency counts (SEPARATE!)
    white_all = []
    pb_all = []

    for _, white, pb in draws:
        white_all.extend(white)
        pb_all.append(pb)

    white_freq = Counter(white_all)
    pb_freq = Counter(pb_all)

    print("Top 10 repeated WHITE BALL numbers (1–69)")
    print("-" * 45)
    for num, count in white_freq.most_common(10):
        print(f"{num} -> {count} times")
    print()

    print("Top 10 repeated POWERBALL numbers (1–26)")
    print("-" * 45)
    for num, count in pb_freq.most_common(10):
        print(f"{num} -> {count} times")

if __name__ == "__main__":
    main()
