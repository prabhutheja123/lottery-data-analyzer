from collections import Counter
import csv
from datetime import datetime

PB_CSV   = "data/nj/powerball.csv"
MEGA_CSV = "data/nj/mega_millions.csv"

def parse_date(d: str) -> datetime:
    d = d.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(d, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unsupported date format: {d}")

def read_powerball(csv_file):
    draws = []
    with open(csv_file, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            d = row["draw_date"].strip()
            white = list(map(int, row["white_numbers"].split()))
            pb = int(row["powerball"])
            draws.append((d, white, pb))
    return draws

def read_mega(csv_file):
    draws = []
    with open(csv_file, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            d = row["draw_date"].strip()
            white = list(map(int, row["white_numbers"].split()))
            mb = int(row["mega_ball"])

            mult_raw = (row.get("multiplier") or "NA").strip()
            mult = int(mult_raw) if mult_raw.isdigit() else None  # None = NA

            draws.append((d, white, mb, mult))
    return draws

def analyze_powerball(draws):
    print("\n===== POWERBALL =====")
    draws = sorted(draws, key=lambda x: parse_date(x[0]), reverse=True)

    print("\nLatest 10 draws")
    print("-" * 55)
    for d, w, pb in draws[:10]:
        print(f"{d} | White: {' '.join(map(str, w))} | PB: {pb}")

    white_all = []
    pb_all = []

    for _, w, pb in draws:
        white_all.extend(w)
        pb_all.append(pb)

    white_freq = Counter(white_all)
    pb_freq = Counter(pb_all)

    print("\nWHITE BALL FREQUENCY (1–69)")
    print("-" * 40)
    for i in range(1, 70):
        print(f"{i:2d} -> {white_freq.get(i, 0)} times")

    print("\nPOWERBALL FREQUENCY (1–26)")
    print("-" * 40)
    for i in range(1, 27):
        print(f"{i:2d} -> {pb_freq.get(i, 0)} times")

def analyze_mega(draws):
    print("\n===== MEGA MILLIONS =====")
    draws = sorted(draws, key=lambda x: parse_date(x[0]), reverse=True)

    print("\nLatest 10 draws")
    print("-" * 70)
    for d, w, mb, mult in draws[:10]:
        mult_str = str(mult) if mult is not None else "NA"
        print(f"{d} | White: {' '.join(map(str, w))} | MB: {mb} | Mult: {mult_str}")

    white_all = []
    mb_all = []
    mult_all = []
    mult_na_count = 0

    for _, w, mb, mult in draws:
        white_all.extend(w)
        mb_all.append(mb)
        if mult is None:
            mult_na_count += 1
        else:
            mult_all.append(mult)

    white_freq = Counter(white_all)
    mb_freq = Counter(mb_all)
    mult_freq = Counter(mult_all)

    print("\nWHITE BALL FREQUENCY (1–70)")
    print("-" * 40)
    for i in range(1, 71):
        print(f"{i:2d} -> {white_freq.get(i, 0)} times")

    print("\nMEGA BALL FREQUENCY (1–25)")
    print("-" * 40)
    for i in range(1, 26):
        print(f"{i:2d} -> {mb_freq.get(i, 0)} times")

    print("\nMEGA MULTIPLIER FREQUENCY")
    print("-" * 40)
    for i in range(2, 6):  # common multipliers
        print(f"{i} -> {mult_freq.get(i, 0)} times")
    print(f"NA -> {mult_na_count} times (missing)")

def main():
    analyze_powerball(read_powerball(PB_CSV))
    analyze_mega(read_mega(MEGA_CSV))

if __name__ == "__main__":
    main()
