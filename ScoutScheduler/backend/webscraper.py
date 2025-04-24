# ScoutScheduler/backend/webscraper.py

"""
Unified web-scraping helpers for Holidays and Badges.
"""

import re
from typing import Dict, Any
import cloudscraper
from requests_html import HTMLSession 
import requests
from bs4 import BeautifulSoup

from .data_store import (
    load_badges, save_badges,
    load_holidays, save_holidays,
)

# --------------------------------------------------------------------------- #
# 1) Harrow council term-dates scraper
# --------------------------------------------------------------------------- #
HARROW_URL = "https://www.harrow.gov.uk/schools-learning/school-term-dates"
def refresh_harrow_holidays() -> list[dict]:
    """
    Renders the Harrow term dates page in a headless browser,
    extracts the date list under 'Term dates', and saves them.
    """

    session = HTMLSession()  # JS-capable behind the scenes :contentReference[oaicite:3]{index=3}
    try:
        r = session.get(HARROW_URL, timeout=30)
        r.html.render(timeout=20)  # execute the client-side scripts :contentReference[oaicite:4]{index=4}
    except Exception:
        # on any failure, return what’s already in holidays.json
        return load_holidays()

    soup = BeautifulSoup(r.html.html, "html.parser")

    # 1) Locate a heading (h1–h4) whose text contains “term date” :contentReference[oaicite:5]{index=5}
    heading = soup.find(
        lambda t: t.name in ("h1","h2","h3","h4")
                  and "term date" in t.get_text(strip=True).lower()
    )
    if not heading:
        return load_holidays()

    # 2) Grab the very next <ul>
    ul = heading.find_next("ul")
    if not ul:
        return load_holidays()

    scraped = []
    for li in ul.find_all("li"):
        text = li.get_text(" ", strip=True)
        # match “18 October 2025 to 4 November 2025” or “18 October to 4 November”
        m = re.search(
            r"(\d{1,2}\s+\w+\s*(?:\d{4})?)\s+to\s+(\d{1,2}\s+\w+\s*(?:\d{4})?)",
            text
        )
        if not m:
            continue
        start_s, end_s = m.groups()

        def parse_date(s: str) -> dt.date:
            for fmt in ("%d %B %Y", "%d %B"):
                try:
                    # if year missing, strptime will fail the first format
                    return dt.datetime.strptime(s, fmt).date()
                except ValueError:
                    continue
            # fallback to today’s year
            return dt.datetime.strptime(f"{s} {dt.date.today().year}", "%d %B %Y").date()

        st = parse_date(start_s)
        en = parse_date(end_s)
        scraped.append({
            "name":  text,
            "start": st.isoformat(),
            "end":   en.isoformat(),
        })

    # 3) If we actually got data, save it; otherwise keep existing :contentReference[oaicite:6]{index=6}
    if scraped:
        save_holidays(scraped)
        return scraped
    else:
        return load_holidays()
# --------------------------------------------------------------------------- #
# 2) Badge catalogue scraper – bypass Cloudflare & hit static pages
# --------------------------------------------------------------------------- #
SECTION_URLS = {
    "Beavers":   "https://www.scouts.org.uk/beavers/activity-badges/",
    "Cubs":      "https://www.scouts.org.uk/cubs/activity-badges/",
    "Scouts":    "https://www.scouts.org.uk/scouts/activity-badges/",
    "Explorers": "https://www.scouts.org.uk/explorers/activity-badges/",
}

def refresh_badge_catalogue() -> Dict[str, Dict[str, Any]]:
    """
    Scrape every section’s static Activity-Badges page to collect
    all badges. Bypasses Cloudflare with cloudscraper.
    """
    scraper = cloudscraper.create_scraper()
    all_badges: Dict[str, Dict[str, Any]] = {}

    for section, url in SECTION_URLS.items():
        resp = scraper.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for h2 in soup.find_all("h2"):
            name = h2.get_text(strip=True)
            if not name or name in all_badges:
                continue

            # grab next <p> or <li> for description
            desc = ""
            sib = h2.find_next_sibling()
            while sib:
                if sib.name in ("p", "li"):
                    desc = sib.get_text(strip=True)
                    break
                sib = sib.find_next_sibling()

            all_badges[name] = {
                "name":         name,
                "sessions":     1,
                "status":       "Not Started",
                "completion":   0,
                "description":  desc,
                "requirements": [],
                "section":      section,
            }

    # merge existing progress
    existing = load_badges()
    for nm, rec in existing.items():
        if nm in all_badges:
            all_badges[nm]["status"]     = rec.get("status", all_badges[nm]["status"])
            all_badges[nm]["completion"] = rec.get("completion", all_badges[nm]["completion"])

    save_badges(all_badges)
    return all_badges
