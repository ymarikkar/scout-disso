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

def refresh_badge_catalogue() -> Dict[str, dict]:
    """
    Scrape the __NEXT_DATA__ JSON from the badge-finder page to load every badge.
    """
    URL = "https://www.scouts.org.uk/activities-and-badges/badge-finder/"

    # 1) fetch the page
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    html = r.text

    # 2) parse the Next.js data blob
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        raise RuntimeError("Could not find __NEXT_DATA__ on badge-finder page")

    data = json.loads(script.string)

    # 3) locate the badge list in the JSON. The exact path may differ; inspect in your browser.
    #    In my tests it's under props.pageProps.allBadges or props.pageProps.badges
    page_props = data.get("props", {}) \
                     .get("pageProps", {})

    badge_items = (
        page_props.get("allBadges")
        or page_props.get("badges")
        or []
    )

    if not badge_items:
        raise RuntimeError("Couldn’t locate badge list in __NEXT_DATA__")

    badges: Dict[str, dict] = {}
    for item in badge_items:
        # Common fields might vary—adjust key names if needed:
        name = item.get("title") or item.get("name")
        if not name:
            continue

        description = item.get("summary") or item.get("description") or ""
        sessions = item.get("hours") or item.get("sessions") or 1

        badges[name] = {
            "name": name,
            "sessions": sessions,
            "status": "Not Started",
            "completion": 0,
            "description": description,
            "requirements": item.get("requirements", []),
        }

    # 4) Merge with any existing local progress, then persist
    from .data_store import load_badges, save_badges
    existing = load_badges()
    for nm, rec in existing.items():
        if nm in badges:
            badges[nm]["status"]     = rec.get("status", badges[nm]["status"])
            badges[nm]["completion"] = rec.get("completion", badges[nm]["completion"])

    save_badges(badges)
    return badges


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
