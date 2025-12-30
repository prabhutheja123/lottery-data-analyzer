import re
import csv
import io
import urllib.request
from urllib.error import HTTPError, URLError
from pathlib import Path

# NY Open Data CSV endpoints (Powerball + Mega Millions)
POWERBALL_URL = "https://data.ny.gov/api/views/d6yy-54nr/rows.csv?accessType=DOWNLOAD"
MEGA_URL = "https://data.ny.gov/api/views/5xaw-6ayf/rows.csv?accessType=DOWNLOAD"

# NJ Lottery official page (Pick-6 page includes recent results + Double Play in HTML)
PICK6_URL = "https://www.njlottery.com/en-us/drawgames/pick6lotto.html"

OUT_DIR = Path("data/nj")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PB_FILE = OUT_DIR / "powerball.csv"
MEGA_FILE = OUT_DIR / "mega_millions.csv"
PICK6_FILE = OUT_DIR / "pick6.csv"


def download(url: str) -> str:
    """
    Download text from a URL. If blocked (e.g., 403) or network fails,
    return empty string so pipeline can continue.
    """
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "close",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read().decode("utf-8", errors="replace")

    except HTTPError as e:
        print(f"⚠️ HTTP error {e.code} for URL: {url}")
        return ""
    except URLError as e:
        print(f"⚠️ Network error for URL: {url} -> {e}")
        return ""
    except Exception as e:
        print(f"⚠️ Unexpected error for URL: {url} -> {repr(e)}")
        return ""


def save_powerball(text: str) -> int:
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
    return count


def save_mega(text: str) -> int:
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
    return count


def save_pick6(html: str) -> int:
    """
    Parse Pick-6 + Double Play from the NJ Lottery HTML page.

    Output columns:
      - draw_date (YYYY-MM-DD)
      - main_numbers (6 nums)
      - double_play_numbers (6 nums)

    If parsing fails or returns 0 rows, save raw HTML for debugging:
      data/nj/pick6_raw.html
    """
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    def to_iso(mmddyyyy: str) -> str:
        mm, dd, yyyy = mmddyyyy.split("/")
        return f"{yyyy}-{mm}-{dd}"

    pattern = re.compile(
        r"(?P<date>\d{2}/\d{2}/\d{4})\s*\.?\s*"
        r"(?P<main>\d{1,2}(?:[,\s]+\d{1,2}){5})"
        r".{0,500}?"
        r"(?:Double\s*Play(?:®)?|\(Double\s*Play\))"
        r".{0,200}?"
        r"(?P<dp>\d{1,2}(?:[,\s]+\d{1,2}){5})",
        re.IGNORECASE | re.DOTALL
    )

    count = 0
    seen = set()

    try:
        matches = list(pattern.finditer(html or ""))

        # ALWAYS create the CSV file (even if no matches)
        with PICK6_FILE.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["draw_date", "main_numbers", "double_play_numbers"])

            for m in matches:
                raw_date = (m.group("date") or "").strip()
                main_nums = re.findall(r"\d+", m.group("main") or "")
                dp_nums = re.findall(r"\d+", m.group("dp") or "")

                if len(main_nums) != 6 or len(dp_nums) != 6:
                    continue

                draw_date = to_iso(raw_date)
                main_str = " ".join(main_nums)
                dp_str = " ".join(dp_nums)

                key = (draw_date, main_str, dp_str)
                if key in seen:
                    continue
                seen.add(key)

                w.writerow([draw_date, main_str, dp_str])
                count += 1

    except Exception as e:
        # Still ensure CSV exists with headers
        with PICK6_FILE.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["draw_date", "main_numbers", "double_play_numbers"])

        raw_path = OUT_DIR / "pick6_raw.html"
        raw_path.write_text(html or "", encoding="utf-8", errors="replace")
        print("⚠️ Pick-6 parsing crashed, but CSV header was created.")
        print("Error:", repr(e))
        print("✅ Debug saved:", raw_path)
        print("✅ Pick-6 rows written: 0")
        return 0

    if count == 0:
        raw_path = OUT_DIR / "pick6_raw.html"
        raw_path.write_text(html or "", encoding="utf-8", errors="replace")
        print("⚠️ Pick-6 parse returned 0 rows (blocked/JS-rendered likely).")
        print("✅ Debug saved:", raw_path)

    print(f"✅ Pick-6 rows written: {count}")
    return count


def main():
    print("=== FETCH NJ LATEST ===")
    print("Output dir:", OUT_DIR.resolve())

    # Powerball
    print("Downloading Powerball...")
    pb_text = download(POWERBALL_URL)
    pb_count = save_powerball(pb_text)
    print("✅ Saved:", PB_FILE.resolve())

    # Mega Millions
    print("Downloading Mega Millions...")
    mega_text = download(MEGA_URL)
    mega_count = save_mega(mega_text)
    print("✅ Saved:", MEGA_FILE.resolve())

    # Pick 6 (may be blocked in GitHub Actions)
    print("Downloading Pick-6 (NJ HTML)...")
    pick6_html = download(PICK6_URL)

    if not pick6_html:
        print("⚠️ Pick-6 download failed/blocked (likely 403). Creating CSV with headers only.")
        pick6_count = save_pick6("")  # creates CSV headers
    else:
        pick6_count = save_pick6(pick6_html)

    print("✅ Saved:", PICK6_FILE.resolve())

    # Fail pipeline ONLY if NY datasets fail (Pick6 can be blocked)
    if pb_count == 0:
        raise RuntimeError("Powerball fetch wrote 0 rows (dataset schema may have changed).")
    if mega_count == 0:
        raise RuntimeError("Mega Millions fetch wrote 0 rows (dataset schema may have changed).")

    print("=== DONE ===")
    print("Counts:")
    print(" - Powerball:", pb_count)
    print(" - Mega Millions:", mega_count)
    print(" - Pick-6:", pick6_count)

    print("Files created in data/nj:")
    for p in sorted(OUT_DIR.glob("*")):
        print(" -", p.name, f"({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
