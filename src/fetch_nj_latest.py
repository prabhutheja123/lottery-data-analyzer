import re
import csv
import io
import urllib.request
from urllib.error import HTTPError, URLError
from pathlib import Path

# ================== URLs ==================
# NY Open Data CSV endpoints (Powerball + Mega Millions)
POWERBALL_URL = "https://data.ny.gov/api/views/d6yy-54nr/rows.csv?accessType=DOWNLOAD"
MEGA_URL = "https://data.ny.gov/api/views/5xaw-6ayf/rows.csv?accessType=DOWNLOAD"

# ✅ Jersey Cash 5 (CSV, stable like PB/Mega)
JERSEY_CASH5_URL = "https://data.ny.gov/api/views/qpqk-8p3g/rows.csv?accessType=DOWNLOAD"

# NJ Lottery official page (Pick-6 page includes recent results + Double Play in HTML)
PICK6_URL = "https://www.njlottery.com/en-us/drawgames/pick6lotto.html"

# ================== PATHS ==================
OUT_DIR = Path("data/nj")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PB_FILE = OUT_DIR / "powerball.csv"
MEGA_FILE = OUT_DIR / "mega_millions.csv"
PICK6_FILE = OUT_DIR / "pick6.csv"
PICK6_RAW = OUT_DIR / "pick6_raw.html"

JC5_FILE = OUT_DIR / "jersey_cash5.csv"


# ================== NETWORK ==================
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
                "Accept": "text/csv,text/plain,text/html,application/json;q=0.9,*/*;q=0.8",
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


def looks_like_csv(text: str, required_cols: list[str]) -> bool:
    if not text:
        return False
    head = text[:4000].lower()
    if "<html" in head or "<!doctype html" in head:
        return False
    return all(col.lower() in head for col in required_cols)


def normalize_multiplier(m: str) -> str:
    """
    Normalize multiplier values to:
      - "2X", "3X", ... or "N/A"
    """
    if not m:
        return "N/A"
    m = m.strip().upper()
    if m in ("NA", "N/A", "NONE"):
        return "N/A"
    digits = re.findall(r"\d+", m)
    if not digits:
        return "N/A"
    return f"{digits[0]}X"


def normalize_xtra(x: str) -> str:
    """
    Normalize XTRA to:
      - "N/A" or a single digit (2/3/4/5 etc)
    """
    if not x:
        return "N/A"
    x = x.strip().upper()
    if x in ("NA", "N/A", "NONE"):
        return "N/A"
    digits = re.findall(r"\d+", x)
    if not digits:
        return "N/A"
    return digits[0]


# ================== SAVE POWERBALL ==================
def save_powerball(text: str) -> int:
    if not looks_like_csv(text, ["Draw Date", "Winning Numbers"]):
        print("⚠️ Powerball response is not a valid CSV (blocked/redirected).")
        with PB_FILE.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["draw_date", "white_numbers", "powerball"])
        return 0

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        print("⚠️ Powerball CSV has no headers.")
        with PB_FILE.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["draw_date", "white_numbers", "powerball"])
        return 0

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


# ================== SAVE MEGA MILLIONS ==================
def save_mega(text: str) -> int:
    if not looks_like_csv(text, ["Draw Date", "Winning Numbers"]):
        print("⚠️ Mega Millions response is not a valid CSV (blocked/redirected).")
        with MEGA_FILE.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["draw_date", "white_numbers", "mega_ball", "multiplier"])
        return 0

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        print("⚠️ Mega Millions CSV has no headers.")
        with MEGA_FILE.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["draw_date", "white_numbers", "mega_ball", "multiplier"])
        return 0

    with MEGA_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", "white_numbers", "mega_ball", "multiplier"])

        count = 0
        for r in reader:
            draw_date = (r.get("Draw Date") or "").strip()
            winning = (r.get("Winning Numbers") or "").strip()
            mega_ball = (r.get("Mega Ball") or "").strip()
            multiplier_raw = (r.get("Multiplier") or "").strip()

            if not draw_date or not winning or not mega_ball:
                continue

            white_nums = re.findall(r"\d+", winning)
            if len(white_nums) != 5:
                continue

            mb = re.findall(r"\d+", mega_ball)
            if not mb:
                continue

            multiplier = normalize_multiplier(multiplier_raw)
            w.writerow([draw_date.split("T")[0], " ".join(white_nums), mb[0], multiplier])
            count += 1

    print(f"✅ Mega Millions rows written: {count}")
    return count


# ================== SAVE JERSEY CASH 5 (CSV) ==================
def save_jersey_cash5(text: str) -> int:
    # Validate CSV
    if not looks_like_csv(text, ["Draw Date", "Winning Numbers"]):
        print("⚠️ Jersey Cash 5 response is not a valid CSV (blocked/redirected).")
        with JC5_FILE.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["draw_date", "numbers", "xtra"])
        return 0

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        print("⚠️ Jersey Cash 5 CSV has no headers.")
        with JC5_FILE.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["draw_date", "numbers", "xtra"])
        return 0

    with JC5_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["draw_date", "numbers", "xtra"])

        count = 0
        for r in reader:
            draw_date = (r.get("Draw Date") or "").split("T")[0].strip()
            winning = (r.get("Winning Numbers") or "").strip()

            # Some datasets use "XTRA" column name; handle both cases
            xtra_raw = (r.get("XTRA") or r.get("Xtra") or r.get("xtra") or "").strip()

            if not draw_date or not winning:
                continue

            nums = re.findall(r"\d+", winning)
            if len(nums) != 5:
                continue

            xtra = normalize_xtra(xtra_raw) if xtra_raw else "N/A"
            w.writerow([draw_date, " ".join(nums), xtra])
            count += 1

    print(f"✅ Jersey Cash 5 rows written: {count}")
    return count


# ================== SAVE PICK 6 ==================
def save_pick6(html: str) -> int:
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
        re.IGNORECASE | re.DOTALL,
    )

    count = 0
    seen = set()

    try:
        matches = list(pattern.finditer(html or ""))

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
        PICK6_RAW.write_text(html or "", encoding="utf-8", errors="replace")
        print("⚠️ Pick-6 parsing crashed.")
        print("Error:", repr(e))
        print("✅ Debug saved:", PICK6_RAW)
        return 0

    if count == 0:
        PICK6_RAW.write_text(html or "", encoding="utf-8", errors="replace")
        print("⚠️ Pick-6 parse returned 0 rows (blocked/JS-rendered likely).")
        print("✅ Debug saved:", PICK6_RAW)

    print(f"✅ Pick-6 rows written: {count}")
    return count


def pick6_cached_has_data(min_bytes: int = 80) -> bool:
    try:
        return PICK6_FILE.exists() and PICK6_FILE.stat().st_size >= min_bytes
    except Exception:
        return False


# ================== MAIN ==================
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

    # ✅ Jersey Cash 5 (CSV)
    print("Downloading Jersey Cash 5...")
    jc5_text = download(JERSEY_CASH5_URL)
    jc5_count = save_jersey_cash5(jc5_text)
    print("✅ Saved:", JC5_FILE.resolve())

    # Pick 6
    print("Downloading Pick-6 (NJ HTML)...")
    pick6_html = download(PICK6_URL)

    if not pick6_html:
        if pick6_cached_has_data():
            print("⚠️ Pick-6 blocked/empty in CI. Keeping existing cached pick6.csv (NOT overwriting).")
            pick6_count = -1
        else:
            print("⚠️ Pick-6 blocked/empty and no cached file found. Creating header-only pick6.csv.")
            with PICK6_FILE.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["draw_date", "main_numbers", "double_play_numbers"])
            pick6_count = 0
    else:
        pick6_count = save_pick6(pick6_html)
        if pick6_count == 0 and pick6_cached_has_data():
            print("⚠️ Pick-6 parse returned 0 but cached pick6.csv exists. Keeping cached file.")

    print("✅ Pick-6 file:", PICK6_FILE.resolve())

    if pb_count == 0:
        print("⚠️ Powerball wrote 0 rows (blocked/unavailable).")
    if mega_count == 0:
        print("⚠️ Mega Millions wrote 0 rows (blocked/unavailable).")
    if jc5_count == 0:
        print("⚠️ Jersey Cash 5 wrote 0 rows (blocked/unavailable).")

    print("=== DONE ===")
    print("Counts:")
    print(" - Powerball:", pb_count)
    print(" - Mega Millions:", mega_count)
    print(" - Jersey Cash 5:", jc5_count)
    print(" - Pick-6:", pick6_count)

    print("Files created in data/nj:")
    for p in sorted(OUT_DIR.glob("*")):
        print(" -", p.name, f"({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
