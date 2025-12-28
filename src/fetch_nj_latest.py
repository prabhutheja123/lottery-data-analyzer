import csv
import io
import urllib.request
from pathlib import Path

POWERBALL_CSV = "https://data.ny.gov/api/views/d6yy-54nr/rows.csv?accessType=DOWNLOAD"

OUT_DIR = Path("data") / "nj"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_POWERBALL = OUT_DIR / "powerball.csv"

def download_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")

def normalize_powerball(csv_text: str) -> None:
    """
    Output columns:
      draw_date, white_numbers, powerball
    """
    reader = csv.DictReader(io.StringIO(csv_text))

    with OUT_POWERBALL.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", "white_numbers", "powerball"])

        for row in reader:
            draw_date = row.get("Draw Date")
            winning = row.get("Winning Numbers")
            if not draw_date or not winning:
                continue

            draw_date = draw_date.split("T")[0]
            parts = winning.split()  # usually 6 parts: 5 white + PB

            if len(parts) < 6:
                continue

            white = " ".join(parts[:5])
            pb = parts[5]

            w.writerow([draw_date, white, pb])

def main():
    print("Downloading Powerball results (NJ uses same draw numbers as all states)...")
    pb_text = download_text(POWERBALL_CSV)
    normalize_powerball(pb_text)
    print("Saved:", OUT_POWERBALL)

if __name__ == "__main__":
    main()
