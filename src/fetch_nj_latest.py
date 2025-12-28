import re
import csv
import io
import urllib.request
from pathlib import Path

# NY Open Data CSV endpoints (Powerball + Mega Millions)
POWERBALL_URL = "https://data.ny.gov/api/views/d6yy-54nr/rows.csv?accessType=DOWNLOAD"
MEGA_URL      = "https://data.ny.gov/api/views/5xaw-6ayf/rows.csv?accessType=DOWNLOAD"

# NJ Lottery official page (Pick-6 page includes recent results + Double Play in HTML)
PICK6_URL = "https://www.njlottery.com/en-us/drawgames/pick6lotto.html"

OUT_DIR = Path("data/nj")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PB_FILE    = OUT_DIR / "powerball.csv"
MEGA_FILE  = OUT_DIR / "mega_millions.csv"
PICK6_FILE = OUT_DIR / "pick6.csv"


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def save_powerball(text):
    reader = csv.DictReader(io.StringIO(text))

    with PB_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", "white_numbers", "powerball"])

        count = 0
        for r in reader:
            nums = (r.get("Winning Numbers") or "").split()
            if len(nums) != 6:
                continue

            draw_date = (r.get("Draw Date") or "").split("T")[0]
            if not draw_date:
                continue

            w.writerow([draw_date, " ".join(nums[:5]), nums[5]])
            count += 1

    print(f"✅ Powerball rows written: {count}")


def save_mega(text):
    reader = csv.DictReader(io.StringIO(text))
    print("Mega CSV columns:", reader.fieldnames)

    with MEGA_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", "white_numbers", "mega_ball", "multiplier"])

        count = 0
        for r in reader:
            draw_date = (r.get("Draw Date") or "").strip()
            winning = (r.get("Winning Numbers") or "").strip()
            mega_ball = (r.get("Mega Ball") or "").strip()
            multiplier = (r.get("Multiplier") or "").strip() or "N/A"

            if not draw_date or not winning or not mega_ball:
                continue

            # Winning Numbers in this dataset = ONLY 5 white balls
            white_nums = re.findall(r"\d+", winning)
            if len(white_nums) != 5:
                continue

            mb = re.findall(r"\d+", mega_ball)
            if not mb:
                continue

            w.writerow([
                draw_date.split("T")[0],
                " ".join(white_nums),
                mb[0],
                multiplier
            ])
            count += 1

    print(f"✅ Mega Millions rows written: {count}")


def save_pick6(html):
    """
    Parse Pick-6 + Double Play from the NJ Lottery HTML page.
    We extract:
      - draw_date (MM/DD/YYYY)
      - 6 main numbers
      - 6 double play numbers
    """
    # This regex tries to find patterns like:
    # 08/30/2025. 03 04 23 40 42 45 ... Double Play ... 02 06 30 32 38 45
    pattern = re.compile(
        r"(\d{2}/\d{2}/\d{4})\.\s*"
        r"([0-9]{1,2}(?:\s+[0-9]{1,2}){5})"
        r".{0,200}?\(Double\s*Play\).*?\s*"
        r"([0-9]{1,2}(?:\s+[0-9]{1,2}){5})",
        re.IGNORECASE | re.DOTALL
    )

    matches = list(pattern.finditer(html))

    with PICK6_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", "main_numbers", "double_play_numbers"])

        count = 0
        for m in matches:
            d = m.group(1).strip()
            main_nums = " ".join(m.group(2).split())
            dp_nums = " ".join(m.group(3).split())

            # sanity: exactly 6 nums each
            if len(main_nums.split()) != 6 or len(dp_nums.split()) != 6:
                continue

            w.writerow([d, main_nums, dp_nums])
            count += 1

    if matches and count == 0:
        print("⚠️ Pick-6 page parsed but 0 rows passed validation (regex matched, but format unexpected).")
    print(f"✅ Pick-6 rows written: {count}")


def main():
    print("Fetching Powerball...")
    save_powerball(download(POWERBALL_URL))
    print("Saved:", PB_FILE)

    print("\nFetching Mega Millions...")
    save_mega(download(MEGA_URL))
    print("Saved:", MEGA_FILE)

    print("\nFetching Pick-6 (NJ)...")
    save_pick6(download(PICK6_URL))
    print("Saved:", PICK6_FILE)


if __name__ == "__main__":
    main()
