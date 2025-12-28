import csv
import urllib.request
from pathlib import Path

DATA_URL = "https://raw.githubusercontent.com/aruljohn/lottery-data/master/USA/powerball.csv"

OUT_DIR = Path("data") / "nj"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "powerball.csv"

def main():
    print("Downloading Powerball data...")
    with urllib.request.urlopen(DATA_URL) as r:
        content = r.read().decode("utf-8")

    lines = content.splitlines()
    reader = csv.DictReader(lines)

    with OUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["draw_date", "numbers"])

        for row in reader:
            # Standard Powerball format
            date = row["Draw Date"]
            nums = [
                row["Winning Number 1"],
                row["Winning Number 2"],
                row["Winning Number 3"],
                row["Winning Number 4"],
                row["Winning Number 5"],
                row["Powerball"],
            ]
            writer.writerow([date, " ".join(nums)])

    print("Saved:", OUT_FILE)

if __name__ == "__main__":
    main()
