from collections import Counter
import csv

# Choose which NJ game file to analyze:
# Examples that will be created:
#   data/nj/pick_3_midday.csv
#   data/nj/pick_3_evening.csv
#   data/nj/pick_4_midday.csv
#   data/nj/pick_4_evening.csv
#   data/nj/jersey_cash_5.csv
#   data/nj/pick_6.csv
#   data/nj/cash4life.csv
#   data/nj/powerball.csv
#   data/nj/mega_millions.csv
INPUT_CSV = "data/nj/powerball.csv"


def read_numbers(csv_path):
    all_numbers = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nums = row["numbers"].replace(",", " ").split()
            for n in nums:
                n = n.strip()
                if n.isdigit():
                    all_numbers.append(int(n))
    return all_numbers


def main():
    numbers = read_numbers(INPUT_CSV)
    freq = Counter(numbers)

    print(f"Analyzing: {INPUT_CSV}")
    print("Top 10 Most Frequent Numbers")
    print("-" * 35)

    for num, count in freq.most_common(10):
        print(f"{num} -> {count} times")


if __name__ == "__main__":
    main()
