import csv
import io
import urllib.request
from pathlib import Path

# Official NY Open Data (safe for GitHub Actions)
POWERBALL_URL = "https://data.ny.gov/api/views/d6yy-54nr/rows.csv?accessType=DOWNLOAD"
MEGA_URL      = "https://data.ny.gov/api/views/5xaw-6ayf/rows.csv?accessType=DOWNLOAD"

OUT_DIR = Path("data") / "nj"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PB_FILE   = OUT_DIR / "powerball.csv"
MEGA_FILE = OUT_DIR / "mega_millions.csv"


def download(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def save_powerball(text):
    reader = csv.DictReader(io.StringIO(text))

    with PB_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", "white_numbers", "powerball"])

        for r in reader:
            nums = r["Winning Numbers"].split()
            if len(nums) < 6:
                continue  # safety check

            draw_date = r["Draw Date"].split("T")[0]
            white = " ".join(nums[:5])
            pb = nums[5]

            w.writerow([draw_date, white, pb])


def save_mega(text):
    reader = csv.DictReader(io.StringIO(text))

    with MEGA_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", "white_numbers", "mega_ball", "multiplier"])

        for r in reader:
            nums = r["Winning Numbers"].split()
            if len(nums) < 6:
                continue  # safety check

            draw_date = r["Draw Date"].split("T")[0]
            white = " ".join(nums[:5])
            mega_ball = nums[5]

            # Multiplier may be missing for old draws
            multiplier = r.get("Multiplier", "").strip()
            multiplier = multiplier if multiplier else "N/A"

            w.writerow([draw_date, white, mega_ball, multiplier])


def main():
    print("Fetching Powerball...")
    save_powerball(download(POWERBALL_URL))
    print("Saved:", PB_FILE)

    print("Fetching Mega Millions...")
    save_mega(download(MEGA_URL))
    print("Saved:", MEGA_FILE)


if __name__ == "__main__":
    main()
