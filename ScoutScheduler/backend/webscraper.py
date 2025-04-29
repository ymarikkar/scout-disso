# ScoutScheduler/backend/webscraper.py

"""
Unified web-scrapers for Holidays and Badges.
"""

import datetime as dt
import json
from datetime import date, timedelta
from typing import Any, Dict

import cloudscraper
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession

from .data_store import load_badges, load_holidays, save_badges, save_holidays

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


# Path to cache JSON file (preserve existing location if defined elsewhere)
HOLIDAYS_CACHE_FILE = (
    "harrow_holidays.json"  # (use the original path from previous code if different)
)


def refresh_harrow_holidays():
    """Fetches the latest Harrow school holiday periods and caches them to a JSON file."""
    url = "https://www.harrow.gov.uk/schools-learning/school-term-dates"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the school year range (e.g., "2024-25") to determine the year for dates
    heading = soup.find(
        lambda tag: tag.name in ["h2", "h3"] and "School year" in tag.text
    )
    if heading:
        # Extract start and end year (e.g., "2024" and "2025")
        text = heading.get_text()
        # Pattern like "2024-25" or "2024-2025"
        import re

        m = re.search(r"(\d{4})-(\d{2}|\d{4})", text)
        if m:
            start_year = int(m.group(1))
            end_year_part = m.group(2)
            end_year = (
                int(end_year_part)
                if len(end_year_part) == 4
                else int(str(start_year)[:2] + end_year_part)
            )
        else:
            # Fallback: if not found, assume current and next year
            start_year = date.today().year
            end_year = start_year + 1
    else:
        # Default to current school year assumption if heading not found
        year = date.today().year
        start_year = year if date.today().month >= 8 else year - 1
        end_year = start_year + 1

    # Parse all list items for term dates
    term_periods = []
    holiday_periods = []
    for li in soup.find_all("li"):
        text = li.get_text(strip=True)
        # Expect format like "Term time: Monday X Mon - Friday Y Mon" or "Half term break: Monday X Mon - Friday Y Mon"
        if ":" in text and "-" in text:
            label, dates = text.split(":", 1)
            label = label.lower()
            dates = dates.strip()
            # Remove day-of-week names for easier parsing
            for day_name in [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]:
                dates = dates.replace(day_name, "")
            dates = dates.replace("to", "-").replace(
                "\u2013", "-"
            )  # normalize any "to" or en-dash to hyphen
            # Now split the two date parts
            try:
                start_str, end_str = [d.strip() for d in dates.split("-")]
            except ValueError:
                continue  # skip if format is not as expected
            # Parse day and month
            try:
                start_day, start_mon = start_str.split()  # e.g., "2 Sep"
                end_day, end_mon = end_str.split()  # e.g., "25 Oct"
            except ValueError:
                continue
            start_day = int(start_day)
            end_day = int(end_day)
            # Map month abbreviation to month number
            mon_map = {
                "Jan": 1,
                "Feb": 2,
                "Mar": 3,
                "Apr": 4,
                "May": 5,
                "Jun": 6,
                "Jul": 7,
                "Aug": 8,
                "Sep": 9,
                "Oct": 10,
                "Nov": 11,
                "Dec": 12,
            }
            if start_mon[:3] not in mon_map or end_mon[:3] not in mon_map:
                continue
            start_month = mon_map[start_mon[:3]]
            end_month = mon_map[end_mon[:3]]
            # Determine year of the dates
            if (
                start_month >= 8
            ):  # August or later -> belongs to the start year (Autumn term months)
                start_date = date(start_year, start_month, start_day)
            else:  # Jan-July -> belongs to the end year (Spring/Summer term months)
                start_date = date(end_year, start_month, start_day)
            # End date likely in same academic year
            if end_month >= 8:
                end_date = date(start_year, end_month, end_day)
            else:
                end_date = date(end_year, end_month, end_day)
            # Categorize term vs holiday
            if "term time" in label:
                term_periods.append((start_date, end_date))
            elif "break" in label or "holiday" in label:
                # Half-term breaks (and any holiday explicitly listed)
                holiday_periods.append((start_date, end_date))
    # Sort the term periods by start date
    term_periods.sort(key=lambda x: x[0])
    # Derive major holiday periods (Christmas, Easter, Summer) that are not explicitly listed as half-term:
    # Christmas break: from end of autumn term to start of spring term
    # Easter break: from end of spring term to start of summer term
    # Summer break: from end of summer term to the end of August (or until next term start if known)
    if term_periods:
        # Find autumn term last day and spring term first day
        autumn_end = None
        spring_start = None
        for s, e in term_periods:
            if e.year == start_year and (autumn_end is None or e > autumn_end):
                autumn_end = e
            if s.year == end_year and (spring_start is None or s < spring_start):
                spring_start = s
        if autumn_end and spring_start:
            # Next Monday after autumn_end
            next_mon = autumn_end + timedelta(days=(7 - autumn_end.weekday()) % 7 or 7)
            # Friday before spring_start
            prev_fri = spring_start - timedelta(
                days=((spring_start.weekday() - 4) % 7 or 7)
            )
            if next_mon <= prev_fri:
                holiday_periods.append((next_mon, prev_fri))  # Christmas break
        # Find spring term last day and summer term first day
        spring_end = None
        summer_start = None
        for s, e in term_periods:
            # Spring term is typically Jan–Mar/Apr (end_year)
            if s.year == end_year and s.month < 4:  # starts in Jan/Feb/March
                if spring_end is None or e > spring_end:
                    spring_end = e
            # Summer term starts in Apr/May (end_year)
            if s.year == end_year and s.month >= 4:
                if summer_start is None or s < summer_start:
                    summer_start = s
        if spring_end and summer_start:
            next_mon = spring_end + timedelta(days=(7 - spring_end.weekday()) % 7 or 7)
            prev_fri = summer_start - timedelta(
                days=((summer_start.weekday() - 4) % 7 or 7)
            )
            if next_mon <= prev_fri:
                holiday_periods.append((next_mon, prev_fri))  # Easter break
        # Summer break: from the day after summer term ends to end of August (assuming new year starts in Sep)
        summer_end = max(e for (_, e) in term_periods)  # last day of final term
        if summer_end:
            summer_break_start = summer_end + timedelta(days=1)
            summer_break_end = date(summer_end.year, 8, 31)
            if summer_break_start <= summer_break_end:
                holiday_periods.append((summer_break_start, summer_break_end))
    # Sort and remove duplicates if any
    holiday_periods = sorted({(s, e) for (s, e) in holiday_periods}, key=lambda x: x[0])
    # Prepare output data (as list of dicts or tuples as needed)
    holidays_data = [{"start": str(s), "end": str(e)} for (s, e) in holiday_periods]
    # Cache to JSON file
    try:
        with open(HOLIDAYS_CACHE_FILE, "w") as f:
            json.dump(holidays_data, f, indent=2)
    except Exception as ex:
        print(f"Warning: could not write cache file: {ex}")
    # Optionally print or log the result count
    print(f"Fetched {len(holiday_periods)} holiday periods.")
    return holidays_data
