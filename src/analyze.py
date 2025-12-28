from collections import Counter
import csv

def read_numbers(csv_path):
    all_numbers = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            numbers = row["numbers"].split()
            all_numbers.extend(int(n) for n in numbers)
    return all_numbers

def main():
    numbers = read_numbers("data/sample.csv")
    freq = Counter(numbers)

    print("Top 10 Most Frequent Numbers")
    print("-" * 35)

    for num, count in freq.most_common(10):
        print(f"{num} -> {count} times")

if __name__ == "__main__":
    main()
