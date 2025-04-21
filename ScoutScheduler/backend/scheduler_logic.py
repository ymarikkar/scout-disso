# ScoutScheduler/backend/scheduler_logic.py

from datetime import datetime, date, timedelta
from collections import defaultdict
from typing import List, Set, Dict

from .data_models import Badge, Session, Preferences

def generate_schedule(
    badges: List[Badge],
    existing_sessions: List[Session],
    holidays: Set[date],
    preferences: Preferences
) -> List[Session]:
    """
    Naïvely schedule one session per incomplete badge, on the next
    available date not in `holidays` or already booked.
    """
    scheduled: List[Session] = []
    today = date.today()

    # build a set of already‑booked dates
    booked: Set[date] = {
        datetime.strptime(s.date, "%d-%m-%Y").date()
        for s in existing_sessions
    }

    next_day = today
    for badge in badges:
        if badge.completed:
            continue

        # find the next free day
        while next_day in holidays or next_day in booked:
            next_day += timedelta(days=1)

        scheduled.append(Session(
            date=next_day.strftime("%d-%m-%Y"),
            time="18:00",                # default time
            title=f"Work on {badge.name}"
        ))
        booked.add(next_day)
        next_day += timedelta(days=1)

    return scheduled
