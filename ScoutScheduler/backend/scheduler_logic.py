import pandas as pd

business_days = pd.bdate_range(
    start="2025-09-01",
    end="2026-07-31",
    freq='B',
    holidays=school_holidays_list
)

from dateutil.rrule import rrule, DAILY
from datetime import datetime

rule = rrule(DAILY, dtstart=datetime(2025,9,1), until=datetime(2026,7,31))
for holiday in school_holidays_list:
    rule = rule.exdate(holiday)
available_dates = list(rule)

def get_available_dates(start, end, holidays):
    # use pandas or dateutil as above
    return date_list

def assign_sessions(badges, available_dates, max_per_week=None):
    # choose greedy or CP method
    return scheduled_sessions  # list of (date, badge_name)
