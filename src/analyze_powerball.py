from collections import Counter
from common import parse_date, read_csv

PB_CSV = "data/nj/powerball.csv"

def main():
    rows = read_csv(PB_CSV)
    draws = []

    for r in rows:
        draws.append((
            r["draw_date"],
            list(map(int, r["white_numbers"].split())),
            int(r["powerball"])
        ))

    draws.sort(key=lambda x: parse_date(x[0]), reverse=True)

    print("\n===== POWERBALL =====")
    print("\nLatest 10 draws")
    print("-" * 40)
    for d, w, pb in draws[:10]:
        print(f"{d} | White: {' '.join(map(str,w))} | PB: {pb}")

    white_all, pb_all = [], []
    for _, w, pb in draws:
        white_all.extend(w)
        pb_all.append(pb)

    print("\nWHITE BALL FREQUENCY (1–69)")
    print("-" * 40)
    wc = Counter(white_all)
    for i in range(1, 70):
        print(f"{i:2d} -> {wc.get(i,0)} times")

    print("\nPOWERBALL FREQUENCY (1–26)")
    print("-" * 40)
    pc = Counter(pb_all)
    for i in range(1, 27):
        print(f"{i:2d} -> {pc.get(i,0)} times")

if __name__ == "__main__":
    main()
