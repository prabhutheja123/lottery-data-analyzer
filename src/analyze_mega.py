from collections import Counter
from common import parse_date, read_csv

MEGA_CSV = "data/nj/mega_millions.csv"

def main():
    rows = read_csv(MEGA_CSV)
    draws = []

    for r in rows:
        draws.append((
            r["draw_date"],
            list(map(int, r["white_numbers"].split())),
            int(r["mega_ball"]),
            int(r["multiplier"]) if r.get("multiplier") else None
        ))

    draws.sort(key=lambda x: parse_date(x[0]), reverse=True)

    print("\n===== MEGA MILLIONS =====")
    print("\nLatest 10 draws")
    print("-" * 40)
    for d, w, mb, m in draws[:10]:
        print(f"{d} | White: {' '.join(map(str,w))} | MB: {mb} | Multiplier: {m}")

    white_all, mb_all, mult_all = [], [], []
    for _, w, mb, m in draws:
        white_all.extend(w)
        mb_all.append(mb)
        if m:
            mult_all.append(m)

    print("\nWHITE BALL FREQUENCY (1–70)")
    print("-" * 40)
    wc = Counter(white_all)
    for i in range(1, 71):
        print(f"{i:2d} -> {wc.get(i,0)} times")

    print("\nMEGA BALL FREQUENCY (1–25)")
    print("-" * 40)
    mc = Counter(mb_all)
    for i in range(1, 26):
        print(f"{i:2d} -> {mc.get(i,0)} times")

    print("\nMEGA MULTIPLIER FREQUENCY")
    print("-" * 40)
    multc = Counter(mult_all)
    for k in sorted(multc):
        print(f"{k}x -> {multc[k]} times")

if __name__ == "__main__":
    main()
