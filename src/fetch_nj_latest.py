import csv
import io
import urllib.request
from pathlib import Path

# NY Open Data CSV endpoints
POWERBALL_URL = "https://data.ny.gov/api/views/d6yy-54nr/rows.csv?accessType=DOWNLOAD"
MEGA_URL      = "https://data.ny.gov/api/views/5xaw-6ayf/rows.csv?accessType=DOWNLOAD"

OUT_DIR = Path("data/nj")
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

        count = 0
        for r in reader:
            nums = r["Winning Numbers"].split()
            if len(nums) != 6:
                continue

            w.writerow([
                r["Draw Date"].split("T")[0],
                " ".join(nums[:5]),
                nums[5]
            ])
            count += 1

    print(f"✅ Powerball rows written: {count}")


def save_mega(text):
    reader = csv.DictReader(io.StringIO(text))

    # DEBUG: show the real Mega CSV columns in Actions logs
    print("Mega CSV columns:", reader.fieldnames)

    with MEGA_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", "white_numbers", "mega_ball", "multiplier"])

        count = 0
        for r in reader:
            # Detect correct column names dynamically (Mega dataset is inconsistent)
            draw_date = (
                r.get("Draw Date") or r.get("draw_date") or r.get("Draw_Date") or r.get("DRAW DATE") or ""
            ).strip()

            winning = (
                r.get("Winning Numbers") or r.get("winning_numbers") or r.get("Winning_Numbers")
                or r.get("WINNING NUMBERS") or ""
            ).strip()

            multiplier = (
                r.get("Multiplier") or r.get("multiplier") or r.get("Megaplier") or r.get("megaplier")
                or r.get("MEGAPLIER") or ""
            ).strip()

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

    print(f"✅ Mega Millions rows written: {count}")


def main():
    print("Fetching Powerball...")
    save_powerball(download(POWERBALL_URL))
    print("Saved:", PB_FILE)

    print("\nFetching Mega Millions...")
    save_mega(download(MEGA_URL))
    print("Saved:", MEGA_FILE)


if __name__ == "__main__":
    main()
