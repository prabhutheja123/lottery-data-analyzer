import re
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


def download(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def save_powerball(text: str) -> None:
    reader = csv.DictReader(io.StringIO(text))

    with PB_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", "white_numbers", "powerball"])

        count = 0
        for r in reader:
            # Powerball dataset uses these columns:
            # Draw Date, Winning Numbers (contains 6 numbers: 5 white + PB)
            draw_date = (r.get("Draw Date") or "").strip()
            winning = (r.get("Winning Numbers") or "").strip()

            nums = winning.split()
            if not draw_date or len(nums) != 6:
                continue

            w.writerow([
                draw_date.split("T")[0],
                " ".join(nums[:5]),
                nums[5]
            ])
            count += 1

    print(f"✅ Powerball rows written: {count}")


def save_mega(text: str) -> None:
    reader = csv.DictReader(io.StringIO(text))
    print("Mega CSV columns:", reader.fieldnames)

    with MEGA_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", "white_numbers", "mega_ball", "multiplier"])

        count = 0
        for r in reader:
            # Mega dataset columns (from your logs):
            # Draw Date, Winning Numbers (5 whites), Mega Ball, Multiplier
            draw_date = (r.get("Draw Date") or "").strip()
            winning = (r.get("Winning Numbers") or "").strip()
            mega_ball = (r.get("Mega Ball") or "").strip()
            multiplier = (r.get("Multiplier") or "").strip() or "N/A"

            if not draw_date or not winning or not mega_ball:
                continue

            # Winning Numbers contains ONLY 5 white balls in this dataset
            white_nums = re.findall(r"\d+", winning)
            if len(white_nums) != 5:
                continue

            # Mega Ball is separate column
            if not mega_ball.isdigit():
                mb = re.findall(r"\d+", mega_ball)
                if not mb:
                    continue
                mega_ball = mb[0]

            w.writerow([
                draw_date.split("T")[0],
                " ".join(white_nums),
                mega_ball,
                multiplier
            ])
            count += 1

    print(f"✅ Mega Millions rows written: {count}")


def main() -> None:
    print("Fetching Powerball...")
    save_powerball(download(POWERBALL_URL))
    print("Saved:", PB_FILE)

    print("\nFetching Mega Millions...")
    save_mega(download(MEGA_URL))
    print("Saved:", MEGA_FILE)

    # Hard verification so CI fails immediately if files are missing
    if not PB_FILE.exists():
        raise FileNotFoundError(f"Expected not found: {PB_FILE}")
    if not MEGA_FILE.exists():
        raise FileNotFoundError(f"Expected not found: {MEGA_FILE}")

    print("\n✅ Verified files exist:")
    print(" -", PB_FILE.resolve())
    print(" -", MEGA_FILE.resolve())


if __name__ == "__main__":
    main()
