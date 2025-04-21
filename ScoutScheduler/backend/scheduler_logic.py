import pandas as pd
from dateutil.rrule import rrule, DAILY
from datetime import datetime, date
from collections import defaultdict
from typing import List, Set, Dict
from .data_models import Badge, Session, Preferences


def generate_schedule(badges, existing_sessions, term_dates, holidays,
                      availability, preferences):
    # 1) Build a flat holiday set
    holiday_set = {d for dates in term_dates.values() for d in dates}

    # 2) Get raw available dates
    start = min(dates[0] for dates in term_dates.values())
    end   = max(dates[-1] for dates in term_dates.values())
    avail = get_available_dates(start, end, holiday_set)

    # 3) Remove any already‑scheduled dates
    existing_dates = {sess.date for sess in existing_sessions}
    avail = [d for d in avail if d not in existing_dates]

    # 4) Assign sessions
    suggestions = assign_sessions(
        badges=badges,
        available_dates=avail,
        max_per_week=preferences.max_per_week
    )

    # 5) Wrap into Session objects, return
    return [Session(date=d, title=f"Work on {badge}") for (d,badge) in suggestions]

def get_available_dates(start: date,
                        end: date,
                        holidays: Set[date]) -> List[date]:
    all_days = pd.bdate_range(start=start, end=end, freq="B")
    return [d.date() for d in all_days if d.date() not in holidays]


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
