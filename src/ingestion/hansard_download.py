"""
Download all Sri Lankan Hansard PDFs from parliament.lk
Organizes files as: output/<YEAR>/<MONTH>/<YYYY_MM_DD_hansard.pdf>

Usage:
    python src/ingestion/hansard_download.py
    python src/ingestion/hansard_download.py --output-dir ./data/raw
    python src/ingestion/hansard_download.py --from-year 2020 --to-year 2026
    python src/ingestion/hansard_download.py --decade 2020s
"""

from __future__ import annotations

import argparse
import os
import time
import random
from datetime import datetime, date
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover - reported before execution
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - reported before execution
    BeautifulSoup = None

BASE_URL = "https://www.parliament.lk/en/business-of-parliament/hansards"
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
EXTRACTED_MARKDOWN_DIR = DATA_DIR / "extracted-markdown"
DEFAULT_OUTPUT_DIR = str(RAW_DATA_DIR)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}
MONTH_NAMES = {
    1: "01_January", 2: "02_February", 3: "03_March", 4: "04_April",
    5: "05_May", 6: "06_June", 7: "07_July", 8: "08_August",
    9: "09_September", 10: "10_October", 11: "11_November", 12: "12_December",
}


def parse_date(date_str: str) -> date | None:
    """Parse date from 'YYYY-MM-DD' or 'Month DD, YYYY' formats."""
    for fmt in ("%Y-%m-%d", "%B %d, %Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def scrape_page(
    session: requests.Session,
    from_date: str,
    to_date: str,
    page: int,
    from_year: int,
    to_year: int,
) -> list[dict]:
    """Scrape a single page and return list of {date, url_pdf} dicts."""
    params = {
        "item_count": 10,
        "from": from_date,
        "to": to_date,
        "page": page,
    }
    try:
        resp = session.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [ERROR] Failed to fetch page {page}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    containers = soup.find_all("div", class_="container")
    if len(containers) < 5:
        return []

    div_container = containers[4]
    docs = []
    for div_row in div_container.find_all("div", class_="row"):
        try:
            h1 = div_row.find("h1")
            if h1 is None:
                continue
            description = h1.get_text().strip()
            if not description.startswith("Hansard of "):
                continue

            date_part = description.replace("Hansard of ", "")
            parsed = parse_date(date_part)
            if parsed is None:
                print(f"  [WARN] Could not parse date: '{date_part}'")
                continue

            div_link = div_row.find("div", class_="align_center_div")
            if div_link is None:
                continue
            a = div_link.find("a")
            if a is None:
                continue
            href = str(a.get("href", ""))
            if not href.endswith(".pdf"):
                continue

            # Keep only requested years in case the website ignores date params.
            if not (from_year <= parsed.year <= to_year):
                continue

            docs.append({"date": parsed, "url_pdf": href})
        except Exception as e:
            print(f"  [WARN] Skipping row: {e}")

    return docs


def collect_all_docs(
    session: requests.Session,
    from_year: int,
    to_year: int,
    max_pages: int,
) -> list[dict]:
    """Scrape all pages within the given year range, return sorted doc list."""
    from_date = f"{from_year}-01-01"
    to_date = f"{to_year}-12-31"
    all_docs = []
    seen_urls = set()
    empty_pages = 0
    no_new_pages = 0

    print(f"\nScraping metadata ({from_date} -> {to_date}) ...")
    page = 1
    while page <= max_pages:
        print(f"  Page {page} ...", end=" ", flush=True)
        docs = scrape_page(
            session=session,
            from_date=from_date,
            to_date=to_date,
            page=page,
            from_year=from_year,
            to_year=to_year,
        )

        if not docs:
            empty_pages += 1
            print("empty")
            if empty_pages >= 3:
                print("  3 consecutive empty pages; stopping.")
                break
        else:
            empty_pages = 0
            new = [d for d in docs if d["url_pdf"] not in seen_urls]
            for d in new:
                seen_urls.add(d["url_pdf"])
            all_docs.extend(new)
            print(f"{len(new)} new doc(s)  [total: {len(all_docs)}]")

            if not new:
                no_new_pages += 1
                if no_new_pages >= 3:
                    print("  3 consecutive pages with 0 new docs; stopping.")
                    break
            else:
                no_new_pages = 0

        page += 1
        time.sleep(random.uniform(0.5, 1.2))  # polite delay

    all_docs.sort(key=lambda d: d["date"])
    return all_docs


def download_pdf(session: requests.Session, url: str, dest_path: str) -> bool:
    """Download a PDF to dest_path. Returns True on success."""
    try:
        resp = session.get(url, headers=HEADERS, timeout=60, stream=True)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if "pdf" not in content_type and not url.endswith(".pdf"):
            print(f"  [WARN] Unexpected content type: {content_type}")
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)
        return True
    except requests.RequestException as e:
        print(f"  [ERROR] Download failed: {e}")
        return False


def download_all(docs: list[dict], output_dir: str) -> None:
    """Download PDFs and create markdown placeholders by Year/Month."""
    total = len(docs)
    skipped = 0
    downloaded = 0
    failed = 0

    print(f"\nDownloading {total} PDF(s) into '{output_dir}' ...\n")

    with requests.Session() as session:
        for i, doc in enumerate(docs, 1):
            d: date = doc["date"]
            year_str = str(d.year)
            month_str = MONTH_NAMES[d.month]
            filename = f"{d.year}_{d.month:02d}_{d.day:02d}.pdf"
            md_filename = f"{d.year}_{d.month:02d}_{d.day:02d}-empty.md"

            folder = os.path.join(output_dir, year_str, month_str)
            os.makedirs(folder, exist_ok=True)
            dest = os.path.join(folder, filename)

            # Keep extracted markdown placeholders in a mirrored folder structure.
            md_folder = os.path.join(str(EXTRACTED_MARKDOWN_DIR), year_str, month_str)
            os.makedirs(md_folder, exist_ok=True)
            md_dest = os.path.join(md_folder, md_filename)
            if not os.path.exists(md_dest):
                with open(md_dest, "w", encoding="utf-8") as f:
                    f.write("")

            prefix = f"[{i}/{total}] {filename}"
            if os.path.exists(dest):
                print(f"  {prefix}  - already exists, skipping")
                skipped += 1
                continue

            print(f"  {prefix}  <- {doc['url_pdf']}")
            ok = download_pdf(session, doc["url_pdf"], dest)
            if ok:
                size_kb = os.path.getsize(dest) / 1024
                print(f"           saved ({size_kb:.0f} KB)")
                downloaded += 1
            else:
                failed += 1

            time.sleep(random.uniform(0.8, 1.5))  # polite delay

    print(f"\n{'='*60}")
    print(f"Done! Downloaded: {downloaded}  |  Skipped: {skipped}  |  Failed: {failed}")
    print(f"Output directory: {os.path.abspath(output_dir)}")


def main():
    parser = argparse.ArgumentParser(
        description="Download Sri Lankan Hansard PDFs organized by Year/Month."
    )
    parser.add_argument(
        "--output-dir", default=DEFAULT_OUTPUT_DIR,
        help=f"Root output folder (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--from-year", type=int, default=2006,
        help="Start year inclusive (default: 2006)"
    )
    parser.add_argument(
        "--to-year", type=int, default=datetime.now().year,
        help=f"End year inclusive (default: {datetime.now().year})"
    )
    parser.add_argument(
        "--decade", choices=["2000s", "2010s", "2020s"],
        help="Shortcut: restrict to a single decade (overrides --from-year/--to-year)"
    )
    parser.add_argument(
        "--max-pages", type=int, default=60,
        help="Maximum metadata pages to scan (default: 60)"
    )
    args = parser.parse_args()
    if requests is None:
        raise SystemExit("Missing dependency: install requests, for example `pip install -r requirements.txt`.")
    if BeautifulSoup is None:
        raise SystemExit("Missing dependency: install beautifulsoup4, for example `pip install -r requirements.txt`.")

    # Ensure core data folders exist.
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(EXTRACTED_MARKDOWN_DIR, exist_ok=True)

    # If user passes the data root, place PDFs under data/raw by default.
    if Path(args.output_dir).resolve() == DATA_DIR.resolve():
        args.output_dir = str(RAW_DATA_DIR)

    if args.decade:
        base = int(args.decade[:3] + "0")
        args.from_year = base
        args.to_year = base + 9

    print("=" * 60)
    print("  LK Hansard PDF Downloader")
    print(f"  Range : {args.from_year} - {args.to_year}")
    print(f"  Output: {os.path.abspath(args.output_dir)}")
    print(f"  Max pages: {args.max_pages}")
    print("=" * 60)

    with requests.Session() as session:
        docs = collect_all_docs(
            session=session,
            from_year=args.from_year,
            to_year=args.to_year,
            max_pages=args.max_pages,
        )

    if not docs:
        print("\nNo documents found. Check your year range or internet connection.")
        return

    print(f"\nFound {len(docs)} document(s) total.")
    download_all(docs, args.output_dir)


if __name__ == "__main__":
    main()
