"""
Tiny module that fetches fresh holiday dates and badge catalogues.

Scraping/network calls are isolated here so importing other modules
never triggers I/O.  Nothing in here is executed unless a Streamlit
button (or a cron job) calls it.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

from .data_store import save_holidays, save_badges, load_badges


# --------------------------------------------------------------------------- #
# 1. UK / GB bank-holiday and school-holiday data
# --------------------------------------------------------------------------- #

BANK_URL = "https://www.gov.uk/bank-holidays.json"  # official JSON feed :contentReference[oaicite:0]{index=0}


def refresh_bank_holidays() -> List[Dict[str, str]]:
    """Return a list[dict] and persist it via data_store.save_holidays()."""
    resp = requests.get(BANK_URL, timeout=30)
    resp.raise_for_status()
    payload = resp.json()

    # Flatten England & Wales only; tweak if your group is elsewhere
    events = payload["england-and-wales"]["events"]
    holidays: List[Dict[str, str]] = [
        {
            "name": e["title"],
            "start": e["date"],
            "end": e["date"],  # single-day for bank hols
        }
        for e in events
        if _dt.date.fromisoformat(e["date"]).year <= _dt.date.today().year + 1
    ]
    save_holidays(holidays)
    return holidays


# --------------------------------------------------------------------------- #
# 2. Badge catalogue from scouts.org.uk (no official API, so basic scrape)
# --------------------------------------------------------------------------- #

CATALOGUE_URL = "https://www.scouts.org.uk/activities-and-badges/badge-finder/"


def _parse_badges(html: str) -> Dict[str, dict]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.badge-card")  # CSS class in current markup
    badges: Dict[str, dict] = {}
    for card in cards:
        name = card.select_one(".badge-name").get_text(strip=True)
        desc = card.select_one(".badge-summary").get_text(strip=True)
        sessions = 1
        # crude heuristic: “x hours” → sessions = ceil(hours/1.5)
        m = re.search(r"(\d+)\s*hour", desc, flags=re.I)
        if m:
            sessions = round(int(m.group(1)) / 1.5)
        badges[name] = {
            "name": name,
            "sessions": sessions,
            "status": "Not Started",
            "completion": 0,
            "description": desc,
            "requirements": [],  # no public list in card; left blank
        }
    return badges


def refresh_badge_catalogue() -> Dict[str, dict]:
    """Scrape the public badge finder and overwrite local catalogue."""
    html = requests.get(CATALOGUE_URL, timeout=30).text
    badges = _parse_badges(html)

    # Merge with local progress if badge already tracked
    existing = load_badges()
    for name, record in badges.items():
        if name in existing:
            record["status"] = existing[name]["status"]
            record["completion"] = existing[name]["completion"]
    save_badges(badges)
    return badges
