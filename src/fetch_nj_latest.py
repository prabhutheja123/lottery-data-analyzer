import csv
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

SOURCE_URL = "https://www.lotterypost.com/results/nj"

OUT_DIR = Path("data") / "nj"
OUT_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class Draw:
    game: str
    draw_date: str  # YYYY-MM-DD
    numbers: list[int]

def fetch_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (GitHubActions; +https://github.com/)"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

def normalize_game_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name).strip("_")
    return name

def parse_date(text: str) -> str:
    # Example: "Saturday, December 27, 2025"
    dt = datetime.strptime(text.strip(), "%A, %B %d, %Y")
    return dt.strftime("%Y-%m-%d")

def parse_latest_results(html: str) -> list[Draw]:
    soup = BeautifulSoup(html, "html.parser")

    draws: list[Draw] = []

    # Game titles are in headings like: "## Pick 3 Midday", "## Powerball"
    # We'll walk h2 blocks and extract nearby date + number bullets.
    for h2 in soup.find_all(["h2"]):
        game = h2.get_text(" ", strip=True)
        if not game:
            continue

        # filter to the NJ games we care about
        wanted = (
            "Pick 3", "Pick 4", "Jersey Cash 5", "Pick 6", "Cash4Life", "Mega Millions", "Powerball"
        )
        if not any(w in game for w in wanted):
            continue

        # find the next text node that looks like a date line
        # Often it appears shortly after the heading.
        date_text = None
        numbers = []

        # search in the next ~25 elements
        cursor = h2
        for _ in range(25):
            cursor = cursor.find_next()
            if cursor is None:
                break

            txt = cursor.get_text(" ", strip=True) if hasattr(cursor, "get_text") else ""
            if date_text is None and re.search(r"^\w+,\s+\w+\s+\d{1,2},\s+\d{4}$", txt):
                date_text = txt
                continue

            # numbers are often in <li> or bullet-style lists; capture standalone integers
            # but stop if we hit the next game heading
            if cursor.name == "h2":
                break

            # Capture list item numbers (e.g., 5 20 34 39 62)
            if cursor.name in ("li", "span", "div"):
                m = re.fullmatch(r"\d{1,2}", txt)
                if m:
                    numbers.append(int(m.group(0)))

        if date_text and numbers:
            draw_date = parse_date(date_text)

            # special handling:
            # - Pick 3 / Pick 4 include "Midday" and "Evening" as separate sections on the page.
            # We keep the game name as-is (e.g., "Pick 3 Midday") so it writes to separate files.
            draws.append(Draw(game=game, draw_date=draw_date, numbers=numbers))

    return draws

def upsert_draw_csv(draw: Draw) -> Path:
    file_name = f"{normalize_game_name(draw.game)}.csv"
    out_path = OUT_DIR / file_name

    existing = set()
    if out_path.exists():
        with out_path.open("r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                existing.add(row["draw_date"])

    # Only append if this draw_date isn't already present
    if draw.draw_date not in existing:
        write_header = not out_path.exists()
        with out_path.open("a", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            if write_header:
                w.writerow(["draw_date", "numbers"])
            w.writerow([draw.draw_date, " ".join(map(str, draw.numbers))])

    return out_path

def main():
    html = fetch_html(SOURCE_URL)
    draws = parse_latest_results(html)

    if not draws:
        raise RuntimeError("No draws parsed. The source page structure may have changed.")

    written = []
    for d in draws:
        written.append(str(upsert_draw_csv(d)))

    print("Updated files:")
    for p in sorted(set(written)):
        print("-", p)

if __name__ == "__main__":
    main()
