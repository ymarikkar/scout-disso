# ScoutScheduler/backend/scheduler_logic.py

from datetime import date, timedelta
from typing import List, Dict
from ScoutScheduler.backend.data_models import Badge, Session

def generate_schedule(
    badges: List[Badge],
    existing_sessions: List[Session],
    term_dates: Dict[str, Dict[str, List[str]]],
    holidays: set,
    preferences,  # refine the type when you’ve modelled Preferences fully
) -> List[Session]:
    """
    Simple placeholder scheduler:
    For each badge not yet completed, pick the next available non-holiday date,
    and schedule a session at 18:00 with title "Work on {badge}".
    """

    scheduled: List[Session] = []
    today = date.today()

    # Build a set of already‑booked dates
    booked = {
        date.fromisoformat(s.date) 
        for s in existing_sessions
        if len(s.date.split("-")) == 3
    }

    # Start looking from tomorrow
    next_day = today + timedelta(days=1)

    for badge in badges:
        if badge.completed:
            continue

        # Skip ahead past holidays or booked days
        while next_day.isoformat() in holidays or next_day in booked:
            next_day += timedelta(days=1)

        # Create a session
        scheduled.append(
            Session(
                date=next_day.strftime("%Y-%m-%d"),
                time="18:00",
                title=f"Work on {badge.name}"
            )
        )

        # Mark this day as booked and advance
        booked.add(next_day)
        next_day += timedelta(days=1)

    return scheduled
