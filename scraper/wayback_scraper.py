"""
wayback_scraper.py

Collects REAL historical job postings via the Wayback Machine (web.archive.org)
instead of scraping live job boards directly, which typically violates their
Terms of Service (LinkedIn, Indeed, and Glassdoor all explicitly prohibit
automated scraping).

How it works:
  1. Query the Wayback Machine's CDX API for archived snapshots of a given
     job posting URL (or search-results URL) across a date range.
  2. Fetch the archived HTML for each snapshot.
  3. Parse out the job description text with BeautifulSoup.

NOTE: You still need to respect the source site's original robots.txt /
ToS where applicable, and this only works for pages that were actually
archived. Company career pages (often less restrictive than LinkedIn/Indeed)
tend to have better archive coverage and are a safer target.

Install deps:
    pip install requests beautifulsoup4 pandas --break-system-packages

Usage:
    python wayback_scraper.py --url "https://example.com/careers/data-analyst" \
        --start 2022 --end 2024 --out ../output/archived_postings.csv
"""

import argparse
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

CDX_API = "http://web.archive.org/cdx/search/cdx"


def get_snapshots(url, start_year, end_year):
    """Query the CDX API for archived snapshot timestamps of a URL."""
    params = {
        "url": url,
        "from": f"{start_year}0101",
        "to": f"{end_year}1231",
        "output": "json",
        "filter": "statuscode:200",
        "collapse": "timestamp:6",  # one snapshot per month-ish
    }
    resp = requests.get(CDX_API, params=params, timeout=30)
    resp.raise_for_status()
    rows = resp.json()
    if not rows or len(rows) < 2:
        return []
    header, *data = rows
    return [dict(zip(header, row)) for row in data]


def fetch_archived_page(timestamp, original_url):
    """Fetch the archived HTML snapshot for a given timestamp."""
    archive_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
    resp = requests.get(archive_url, timeout=30, headers={
        "User-Agent": "Mozilla/5.0 (research; skill-inflation-index project)"
    })
    resp.raise_for_status()
    return resp.text, archive_url


def extract_description(html):
    """
    Best-effort extraction of job description text.
    You will likely need to customize the selector per site structure —
    job boards vary widely. This grabs the largest text block as a fallback.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Try common containers first
    for selector in ["[class*='description']", "[id*='description']",
                      "[class*='job-details']", "article", "main"]:
        el = soup.select_one(selector)
        if el and len(el.get_text(strip=True)) > 200:
            return el.get_text(separator=" ", strip=True)

    # Fallback: largest <div> by text length
    candidates = soup.find_all(["div", "section"])
    if not candidates:
        return ""
    best = max(candidates, key=lambda t: len(t.get_text(strip=True)))
    return best.get_text(separator=" ", strip=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Original job posting URL to look up in the archive")
    parser.add_argument("--start", type=int, default=2022)
    parser.add_argument("--end", type=int, default=2024)
    parser.add_argument("--out", default="../output/archived_postings.csv")
    parser.add_argument("--delay", type=float, default=1.5, help="Seconds between requests (be polite)")
    args = parser.parse_args()

    snapshots = get_snapshots(args.url, args.start, args.end)
    print(f"Found {len(snapshots)} snapshots for {args.url}")

    rows = []
    for snap in snapshots:
        ts = snap["timestamp"]
        try:
            html, archive_url = fetch_archived_page(ts, args.url)
            description = extract_description(html)
            rows.append({
                "source_url": args.url,
                "archive_url": archive_url,
                "timestamp": ts,
                "date": f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}",
                "description": description,
            })
            print(f"  Fetched snapshot {ts} ({len(description)} chars)")
        except Exception as e:
            print(f"  Failed snapshot {ts}: {e}")
        time.sleep(args.delay)

    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)
    print(f"Saved {len(df)} archived postings -> {args.out}")


if __name__ == "__main__":
    main()
