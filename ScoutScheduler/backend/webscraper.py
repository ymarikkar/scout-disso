# ScoutScheduler/backend/webscraping.py

import datetime as dt
from typing import Dict, Any
import cloudscraper
from bs4 import BeautifulSoup

from .data_store import load_badges, save_badges

# These static pages list every badge with an <h2> name and a <p> description
SECTION_URLS = {
    "Beavers":   "https://www.scouts.org.uk/beavers/activity-badges/",
    "Cubs":      "https://www.scouts.org.uk/cubs/activity-badges/",
    "Scouts":    "https://www.scouts.org.uk/scouts/activity-badges/",
    "Explorers": "https://www.scouts.org.uk/explorers/activity-badges/",
}

def refresh_badge_catalogue() -> Dict[str, Dict[str, Any]]:
    """
    Bypass Cloudflare with cloudscraper, fetch each section’s static page,
    parse every <h2> + next <p> (or <li>) for name/description,
    merge in existing progress, and save to data/badges.json.
    """
    scraper = cloudscraper.create_scraper()  # handles Cloudflare
    all_badges: Dict[str, Dict[str, Any]] = {}

    for section, url in SECTION_URLS.items():
        r = scraper.get(url, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for h2 in soup.find_all("h2"):
            name = h2.get_text(strip=True)
            if not name or name in all_badges:
                continue

            # grab first <p> or <li> sibling for description
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

    # merge existing progress so you don’t lose any completions
    existing = load_badges()
    for nm, rec in existing.items():
        if nm in all_badges:
            all_badges[nm]["status"]     = rec.get("status", all_badges[nm]["status"])
            all_badges[nm]["completion"] = rec.get("completion", all_badges[nm]["completion"])

    save_badges(all_badges)
    return all_badges
