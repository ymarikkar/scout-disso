#!/usr/bin/env python3

import sys
from pathlib import Path

# 1) Make sure the ScoutScheduler package root is on PYTHONPATH
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def initialise_data():
    # 2) Pull in the latest badge & holiday data
    from backend.webscraping import fetch_badge_data, fetch_school_holidays

    print("↻ Refreshing badge data…")
    try:
        n_badges = fetch_badge_data()
        print(f"   → Saved {len(n_badges)} badges")
    except Exception as e:
        print("   ! Failed to fetch badges:", e)

    print("↻ Refreshing holiday data…")
    try:
        holiday_dict = fetch_school_holidays()
        total_terms = len(holiday_dict)
        print(f"   → Saved {total_terms} term entries")
    except Exception as e:
        print("   ! Failed to fetch holidays:", e)

def main():
    print("▶ Starting Scout Scheduler")
    initialise_data()

    # 3) Launch the GUI
    from gui.scheduler import launch_scheduler
    print("▶ Launching GUI…")
    launch_scheduler()

if __name__ == "__main__":
    main()
