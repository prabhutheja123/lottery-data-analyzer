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
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")

def save_powerball(text):
    reader = csv.DictReader(io.StringIO(text))
    with PB_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", "white_numbers", "powerball"])

        for r in reader:
            draw_date = (r.get("Draw Date") or "").strip()
            winning = (r.get("Winning Numbers") or "").strip()

            nums = winning.split()
            # ✅ safety: must have 6 numbers (5 white + PB)
            if len(nums) != 6 or not draw_date:
                continue

            w.writerow([
                draw_date.split("T")[0],
                " ".join(nums[:5]),
                nums[5]
            ])

def save_mega(text):
    reader = csv.DictReader(io.StringIO(text))
    with MEGA_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        # ✅ added multiplier column
        w.writerow(["draw_date", "white_numbers", "mega_ball", "multiplier"])

        for r in reader:
            draw_date = (r.get("Draw Date") or "").strip()
            winning = (r.get("Winning Numbers") or "").strip()
            multiplier = (r.get("Multiplier") or "").strip()  # ✅ Mega multiplier

            nums = winning.split()
            # ✅ safety: must have 6 numbers (5 white + Mega Ball)
            if len(nums) != 6 or not draw_date:
                continue

            w.writerow([
                draw_date.split("T")[0],
                " ".join(nums[:5]),
                nums[5],
                multiplier if multiplier else "NA"
            ])

def main():
    print("Fetching Powerball...")
    save_powerball(download(POWERBALL_URL))
    print("Saved:", PB_FILE)

    print("Fetching Mega Millions...")
    save_mega(download(MEGA_URL))
    print("Saved:", MEGA_FILE)

if __name__ == "__main__":
    main()
