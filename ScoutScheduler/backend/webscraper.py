# ScoutScheduler/backend/webscraper.py

"""
Unified web-scraping helpers for Holidays and Badges.
"""

import re
from typing import Dict, Any
import cloudscraper
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
    Scrape Harrow Council's “Term dates” section by:
     • Bypassing CF with cloudscraper
     • Locating 'term date' heading (h1–h4)
     • Parsing its first <ul> of <li> date ranges
    """
    scraper = cloudscraper.create_scraper()
    resp = scraper.get(HARROW_URL, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) Find any heading containing 'term date'
    heading = soup.find(
        lambda t: t.name in ("h1","h2","h3","h4")
                 and "term date" in t.get_text(strip=True).lower()
    )
    if not heading:
        raise RuntimeError("Could not find 'Term dates' heading on Harrow page")

    # 2) Grab the very next <ul>
    ul = heading.find_next("ul")
    if not ul:
        raise RuntimeError("Could not find holiday list after the heading")

    holidays: list[dict] = []
    for li in ul.find_all("li"):
        text = li.get_text(" ", strip=True)
        # e.g. "Monday 18 October to Friday 22 October"
        m = re.search(r"(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2}\s+\w+)\s+to\s+(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2}\s+\w+)", text)
        if not m:
            continue
        start_s, end_s = m.groups()

        # If year is missing (e.g. "18 October"), append current year
        def parse_date(s: str) -> dt.date:
            try:
                return dt.datetime.strptime(s, "%d %B %Y").date()
            except ValueError:
                return dt.datetime.strptime(f"{s} {dt.date.today().year}", "%d %B %Y").date()

        start = parse_date(start_s)
        end   = parse_date(end_s)

        holidays.append({
            "name":  text,
            "start": start.isoformat(),
            "end":   end.isoformat(),
        })

    # Persist via data_store
    save_holidays(holidays)
    return holidays

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
