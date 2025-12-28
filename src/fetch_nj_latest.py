import csv
import io
import urllib.request
from pathlib import Path

# NY Open Data (Socrata) CSV downloads
POWERBALL_CSV = "https://data.ny.gov/api/views/d6yy-54nr/rows.csv?accessType=DOWNLOAD"

# If you later want Mega Millions too, we can add its dataset id the same way.
# (We’ll add once you confirm Powerball works end-to-end.)

OUT_DIR = Path("data") / "nj"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_POWERBALL = OUT_DIR / "powerball.csv"

def download_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")

def normalize_powerball(csv_text: str) -> None:
    """
    Input columns (from NY Open Data):
      - Draw Date
      - Winning Numbers  (example: "05 20 34 39 62 01")  <- last is PB
      - Multiplier (optional)
    Output:
      draw_date,numbers
      YYYY-MM-DD, "n1 n2 n3 n4 n5 pb"
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    with OUT_POWERBALL.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", "numbers"])

        for row in reader:
            draw_date = row.get("Draw Date") or row.get("draw_date")
            winning = row.get("Winning Numbers") or row.get("winning_numbers")
            if not draw_date or not winning:
                continue

            nums = " ".join(winning.split())
            # draw_date from Socrata often like "2025-12-27T00:00:00.000"
            draw_date = draw_date.split("T")[0]
            w.writerow([draw_date, nums])

def main():
    print("Downloading Powerball results (NJ uses same draw numbers as all states)...")
    pb_text = download_text(POWERBALL_CSV)
    normalize_powerball(pb_text)
    print("Saved:", OUT_POWERBALL)

if __name__ == "__main__":
    main()
