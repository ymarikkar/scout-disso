import pandas as pd
from collections import defaultdict
from datetime import timedelta

business_days = pd.bdate_range(
    start="2025-09-01",
    end="2026-07-31",
    freq='B',
    holidays=school_holidays_list
)

from dateutil.rrule import rrule, DAILY
from datetime import datetime

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


rule = rrule(DAILY, dtstart=datetime(2025,9,1), until=datetime(2026,7,31))
for holiday in school_holidays_list:
    rule = rule.exdate(holiday)
available_dates = list(rule)

def get_available_dates(start: str, end: str, holidays: Set[date]) -> List[date]:
    # 1) Generate all weekdays
    all_days = pd.bdate_range(start=start, end=end, freq="B")
    # 2) Drop any that fall in `holidays`
    available = [d.date() for d in all_days if d.date() not in holidays]
    return available


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
