import csv
import io
import urllib.request
from pathlib import Path

POWERBALL_URL = "https://data.ny.gov/api/views/d6yy-54nr/rows.csv?accessType=DOWNLOAD"
MEGA_URL      = "https://data.ny.gov/api/views/5xaw-6ayf/rows.csv?accessType=DOWNLOAD"

OUT_DIR = Path("data") / "nj"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PB_FILE   = OUT_DIR / "powerball.csv"
MEGA_FILE = OUT_DIR / "mega_millions.csv"


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def pick_col(row, candidates):
    """Return the first existing column name from candidates."""
    for c in candidates:
        if c in row and row[c]:
            return row[c]
    return ""


def save_powerball(text):
    reader = csv.DictReader(io.StringIO(text))
    with PB_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", "white_numbers", "powerball"])

        count = 0
        for r in reader:
            draw_date = pick_col(r, ["Draw Date", "draw_date", "Draw_Date"])
            winning   = pick_col(r, ["Winning Numbers", "winning_numbers", "Winning_Numbers"])

            nums = winning.split()
            if len(nums) != 6 or not draw_date:
                continue

            w.writerow([draw_date.split("T")[0], " ".join(nums[:5]), nums[5]])
            count += 1

    print("Powerball rows written:", count)


def save_mega(text):
    reader = csv.DictReader(io.StringIO(text))
    with MEGA_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", "white_numbers", "mega_ball", "multiplier"])

        count = 0
        for r in reader:
            draw_date = pick_col(r, ["Draw Date", "draw_date", "Draw_Date"])
            winning   = pick_col(r, ["Winning Numbers", "winning_numbers", "Winning_Numbers"])

            # multiplier column name differs across datasets
            multiplier = pick_col(r, ["Multiplier", "multiplier", "Megaplier", "megaplier", "Mega Multiplier"])

            nums = winning.split()
            if len(nums) != 6 or not draw_date:
                continue

            w.writerow([
                draw_date.split("T")[0],
                " ".join(nums[:5]),
                nums[5],
                multiplier if multiplier else "N/A"
            ])
            count += 1

    print("Mega Millions rows written:", count)


def main():
    print("Fetching Powerball...")
    save_powerball(download(POWERBALL_URL))
    print("Saved:", PB_FILE)

    print("Fetching Mega Millions...")
    save_mega(download(MEGA_URL))
    print("Saved:", MEGA_FILE)


if __name__ == "__main__":
    main()
