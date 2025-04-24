"""
Unified scraper for badges and holidays.
Uses data_store helpers so Streamlit pages see the same JSON files.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from .data_store import save_badges, save_holidays, load_badges

import json
import requests
from bs4 import BeautifulSoup
from typing import Dict

FINDER_URL = "https://www.scouts.org.uk/activities-and-badges/badge-finder/"
# ScoutScheduler/backend/webscraping.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, Any

from .data_store import load_badges, save_badges

# STATIC PAGES for all sections
SECTION_URLS = {
    "Beavers":   "https://www.scouts.org.uk/beavers/activity-badges/",
    "Cubs":      "https://www.scouts.org.uk/cubs/activity-badges/",
    "Scouts":    "https://www.scouts.org.uk/scouts/activity-badges/",
    "Explorers": "https://www.scouts.org.uk/explorers/activity-badges/",
}

def refresh_badge_catalogue() -> Dict[str, Dict[str, Any]]:
    """
    Scrape the static Activity-Badges pages to collect every badge name
    and its description. Merges in any existing progress data.
    """
    all_badges: Dict[str, Dict[str, Any]] = {}

    for section, url in SECTION_URLS.items():
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # On these pages, badge names are in <h2> and a <p> follows with desc
        for h2 in soup.find_all("h2"):
            name = h2.get_text(strip=True)
            if not name or name in all_badges:
                continue

            # Find the first <p> (or <li>) sibling for description
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

    # Merge existing progress
    existing = load_badges()
    for nm, rec in existing.items():
        if nm in all_badges:
            all_badges[nm]["status"]     = rec.get("status", all_badges[nm]["status"])
            all_badges[nm]["completion"] = rec.get("completion", all_badges[nm]["completion"])

    # Persist and return
    save_badges(all_badges)
    return all_badges



# --------------------------------------------------------------------------- #
# Holiday scraper — Harrow Council web page
# --------------------------------------------------------------------------- #

HARROW_URL = (
    "https://www.harrow.gov.uk/schools-learning/school-term-dates"
)  # update if your council changes path


def refresh_harrow_holidays() -> List[dict]:
    """Scrape term dates from Harrow Council; return list[dict] & persist."""
    html = requests.get(HARROW_URL, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")
    box = soup.find("div", class_="harrow-info-box--key-info")

    if not box:
        raise RuntimeError("Term-date box not found – page structure changed")

    holidays: List[dict] = []
    year_header = box.find("h3").get_text(strip=True)
    content = box.find("div", class_="harrow-info-box__content")

    for p in content.find_all("p"):
        term = p.find("strong")
        if not term:
            continue
        term_name = term.get_text(strip=True)
        ul = p.find_next_sibling("ul")
        if not ul:
            continue
        for li in ul.find_all("li"):
            span = li.get_text(strip=True)
            # Expect “Monday 15 April to Friday 24 May 2025”
            m = re.match(
                r".*?(\d{1,2}\s+\w+\s+\d{4}).*?(\d{1,2}\s+\w+\s+\d{4})", span
            )
            if not m:
                continue
            start, end = m.groups()
            holidays.append(
                {
                    "name": f"{term_name} ({year_header})",
                    "start": dt.datetime.strptime(start, "%d %B %Y")
                    .date()
                    .isoformat(),
                    "end": dt.datetime.strptime(end, "%d %B %Y")
                    .date()
                    .isoformat(),
                }
            )

    save_holidays(holidays)
    return holidays


# --------------------------------------------------------------------------- #
# Badge catalogue scraper  (Scouts UK site)
# --------------------------------------------------------------------------- #

CATALOGUE_URL = "https://www.scouts.org.uk/activities-and-badges/badge-finder/"


def _parse_badges(html: str) -> Dict[str, dict]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.badge-card")
    data: Dict[str, dict] = {}
    for card in cards:
        name = card.select_one(".badge-name").get_text(strip=True)
        desc = card.select_one(".badge-summary").get_text(strip=True)
        # Very rough heuristic for sessions:
        sessions = 1 + desc.lower().count("skills")
        data[name] = {
            "name": name,
            "sessions": sessions,
            "status": "Not Started",
            "completion": 0,
            "description": desc,
            "requirements": [],
        }
    return data


def refresh_badge_catalogue() -> Dict[str, dict]:
    html = requests.get(CATALOGUE_URL, timeout=30).text
    new_badges = _parse_badges(html)

    # merge progress from existing local file
    existing = load_badges()
    for name in existing:
        if name in new_badges:
            new_badges[name]["status"] = existing[name].get("status", "Not Started")
            new_badges[name]["completion"] = existing[name].get("completion", 0)

    save_badges(new_badges)
    return new_badges

# ScoutScheduler/backend/webscraping.py

def _parse_badges(html: str) -> Dict[str, dict]:
    """
    Fallback parser: grab every H2 as a badge name, and the first
    <p> (or <li>) that follows it as the description.
    """
    soup = BeautifulSoup(html, "html.parser")

    # The badge names on the finder page use <h2> tags
    headers = soup.find_all("h2")
    badges: Dict[str, dict] = {}

    for header in headers:
        name = header.get_text(strip=True)
        if not name:
            continue

        # Look for the next paragraph or list item for description
        desc = ""
        sib = header.find_next_sibling()
        while sib:
            if sib.name in ("p", "li"):
                desc = sib.get_text(strip=True)
                break
            sib = sib.find_next_sibling()

        badges[name] = {
            "name": name,
            "sessions": 1,
            "status": "Not Started",
            "completion": 0,
            "description": desc,
            "requirements": [],
        }

    return badges
