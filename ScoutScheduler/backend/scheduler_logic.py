import pandas as pd
from dateutil.rrule import rrule, DAILY
from datetime import datetime, date
from collections import defaultdict
from typing import List, Set, Dict
from .data_models import Badge, Session, Preferences
from ScoutScheduler.backend.scheduler_logic import generate_schedule
from ScoutScheduler.backend.data_management import load_badges, load_term_dates
from ScoutScheduler.backend.data_models     import Preferences


ddef generate_schedule(
    badges: List[Badge],
    existing_sessions: List[Session],
    term_dates: Dict[str, Dict[str, List[str]]],
    holidays: set,
    preferences,  # you can type this later
) -> List[Session]:
    """
    A naive proposer: for each badge not yet done, 
    schedule one session each on the next available non‑holiday date.
    """
    scheduled: List[Session] = []
    today = date.today()
    # build a set of dates already booked
    booked = {datetime.strptime(s.date, "%d-%m-%Y").date() for s in existing_sessions}

    next_day = today
    for badge in badges:
        # skip badges already completed
        if badge.completed:
            continue

        # find the next free date
        while next_day in holidays or next_day in booked:
            next_day += timedelta(days=1)

        # make one Session
        scheduled.append(
            Session(
                date=next_day.strftime("%d-%m-%Y"), 
                time="18:00",  # default slot
                title=f"Work on {badge.name}"
            )
        )

        # mark it booked
        booked.add(next_day)
        next_day += timedelta(days=1)

    return scheduled


def assign_sessions(badges, available_dates, max_per_week=None):
    # Map badge → remaining sessions
    remaining = {b.name: b.sessions_required for b in badges}
    schedule = []
    week_counts = defaultdict(int)  # count per (year, week) if max_per_week

    for dt in available_dates:
        # enforce weekly cap
        year, week, _ = dt.isocalendar()
        if max_per_week and week_counts[(year,week)] >= max_per_week:
            continue

        # pick next badge needing sessions
        for badge in sorted(badges, key=lambda b: b.sessions_required, reverse=True):
            if remaining[badge.name] > 0:
                schedule.append((dt, badge.name))
                remaining[badge.name] -= 1
                week_counts[(year,week)] += 1
                break

        # stop early if all done
        if all(v == 0 for v in remaining.values()):
            break

    return schedule
