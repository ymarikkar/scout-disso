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
import datetime as dt
import re

from .data_store import (
    load_badges, save_badges,
    load_holidays, save_holidays,
)

# --------------------------------------------------------------------------- #
# 1) Harrow council term-dates scraper
# --------------------------------------------------------------------------- #
HARROW_URL = "https://www.harrow.gov.uk/schools-learning/school-term-dates"


def _parse_date(s: str) -> dt.date:
    """Parse '2 Sep 2024' or '2 September 2024' into a date."""
    for fmt in ("%d %b %Y", "%d %B %Y", "%d %b", "%d %B"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    # fallback: attach current year
    return dt.datetime.strptime(f"{s} {dt.date.today().year}", "%d %B %Y").date()

def refresh_harrow_holidays() -> list[dict]:
    # 1. render the live page
    session = HTMLSession()
    try:
        r = session.get(HARROW_URL, timeout=30)
        r.html.render(timeout=20)
    except Exception:
        return load_holidays()

    soup = BeautifulSoup(r.html.html, "html.parser")

    # 2. find the “School year 2024-25” heading
    year_heading = soup.find("h3", string=re.compile(r"School year", re.I))
    if not year_heading:
        return load_holidays()

    # 3. walk siblings until the next h3 (Future school term dates)
    periods = []
    current_term = None
    for sib in year_heading.next_siblings:
        if isinstance(sib, Tag) and sib.name == "h3":
            # reached the “Future school term dates” heading → stop
            break

        if isinstance(sib, Tag) and sib.name in ("h4", "p"):
            text = sib.get_text(" ", strip=True)

            # if it's a term title (e.g. “Autumn Term 2024”), remember it
            m_term = re.match(r"^(Autumn|Spring|Summer)\s+Term", text, re.I)
            if m_term:
                current_term = text
                continue

            # if it's a bullet-list line starting with “* ” or “• ”
            # some themes render bullets as paragraphs prefixed with “*”
            bullet = re.sub(r'^[\*\u2022]\s*', "", text)
            for kind in ("Half term break", "Term time"):
                if bullet.startswith(kind):
                    # extract the two dates
                    m = re.search(rf"{kind}:\s*(.*?)\s*-\s*(.*)", bullet)
                    if not m:
                        continue
                    start_s, end_s = m.groups()
                    start_d = _parse_date(start_s)
                    end_d   = _parse_date(end_s)

                    # we only want the *breaks*, not the term-times
                    if kind.lower().startswith("half term"):
                        name = f"{current_term} – Half-term break"
                        periods.append(
                            {"name": name,
                             "start": start_d.isoformat(),
                             "end":   end_d.isoformat()}
                        )
                    # for summer, infer the full break (post-term to next autumn)
                    elif kind.lower().startswith("term time") and "summer" in current_term.lower():
                        # summer break starts the next day
                        sbeg = end_d + dt.timedelta(days=1)
                        # find next autumn start from a sibling link
                        # simplest: hard-code next known date from the page
                        # or skip inference here
                        continue

    # 4. (Optionally) infer the summer break from the end of summer term:
    #     - last bullet "Term time: … - DD July"
    #     - next Autumn Term start = first term-time date in Autumn Term
    # Here’s one naive way:
    if periods:
        # find the summer-term end line
        summer_end = None
        for sib in year_heading.next_siblings:
            if isinstance(sib, Tag) and "Summer Term" in sib.get_text():
                # look for next bullet
                for inner in sib.find_next_siblings():
                    t = inner.get_text(" ", strip=True)
                    if t.startswith(("Term time", "* Term time", "• Term time")):
                        dd = re.sub(r'^(?:Term time:|\*\s*Term time:)\s*', "", t)
                        m = re.match(r"(.*?)\s*-\s*(.*)", dd)
                        if m:
                            start_s, end_s = m.groups()
                            summer_end = _parse_date(end_s)
                        break
                break
        # assume Autumn start is the first Term-time in Autumn:
        autumn_start = None
        for sib in year_heading.next_siblings:
            if isinstance(sib, Tag) and "Autumn Term" in sib.get_text():
                for inner in sib.find_next_siblings():
                    tt = inner.get_text(" ", strip=True)
                    if tt.startswith(("Term time", "* Term time")):
                        m = re.search(r"(.*?)\s*-\s*(.*)", tt)
                        if m:
                            autumn_start = _parse_date(m.group(1))
                        break
                break
        if summer_end and autumn_start and autumn_start > summer_end:
            periods.append({
                "name":      "Summer break",
                "start":     (summer_end + dt.timedelta(days=1)).isoformat(),
                "end":       (autumn_start - dt.timedelta(days=1)).isoformat()
            })

    # 5. if we found *any* break periods, save them; otherwise keep existing
    if periods:
        save_holidays(periods)
        return periods
    else:
        return load_holidays()
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
