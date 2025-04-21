# ScoutScheduler/backend/data_management.py
from typing import List, Dict
from datetime import date
from .data_models import Badge, Session

from typing import List, Dict  # ← you need this for your function annotations

import json
import os
from pathlib import Path

# Path to scraped badge definitions
BADGE_DEFS = Path(__file__).parent / "data" / "badge_data.json"
# Path to user’s badge-completion status
BADGE_STATUS = Path(__file__).parent / "data" / "badge_status.json"
# (existing session file path)
SESSION_FILE = Path(__file__).parent / "data" / "sessions.json"

# in ScoutScheduler/backend/data_management.py
from datetime import datetime

def load_badges() -> List[Badge]:
    with open("data/badge_data.json", "r") as f:
        raw = json.load(f)
    # assume raw is { badge_name: url, … }
    return [ Badge(name=k, sessions_required=Badge.lookup_sessions(k)) for k in raw ]

def load_term_dates() -> Dict[str, List[date]]:
    with open("data/holiday_data.json", "r") as f:
        raw = json.load(f)
    # raw is { "School year 2024-25": { "Autumn Term 2024": [ … ], … } }
    term_dates = {}
    for year, terms in raw.items():
        term_dates[year] = []
        for dates in terms.values():
            for line in dates:
                # parse “Term time: Monday 2 Sep – Friday 25 Oct”
                parts = line.split(":")[1].strip().split(" - ")
                start = datetime.strptime(parts[0], "%A %d %b").replace(year=int(year[:4])).date()
                end   = datetime.strptime(parts[1], "%A %d %b").replace(year=int(year[:4])).date()
                term_dates[year].extend([start, end])
    return term_dates

def load_sessions():
    """
    Load the list of scheduled sessions from disk.
    Returns an empty list if no file exists.
    """
    if SESSIONS_FILE.exists():
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_sessions(sessions):
    """
    Save the list of sessions (a Python list) back to disk as JSON.
    Creates the data directory if needed.
    """
    os.makedirs(SESSIONS_FILE.parent, exist_ok=True)
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=4)

def load_badges():
    """
    Returns a dict mapping badge-name -> bool (True if completed).
    If no status file exists, initialize all badges to False.
    """
    if BADGE_STATUS.exists():
        with open(BADGE_STATUS, encoding="utf-8") as f:
            return json.load(f)
    # No status file yet: read definitions and init all to False
    with open(BADGE_DEFS, encoding="utf-8") as f:
        defs = json.load(f)
    status = {name: False for name in defs.keys()}
    return status

def save_badges(status: dict):
    """
    Persists the badge-status dict to JSON.
    """
    os.makedirs(BADGE_STATUS.parent, exist_ok=True)
    with open(BADGE_STATUS, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)
