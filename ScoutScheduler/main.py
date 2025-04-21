#!/usr/bin/env python3
import sys
from pathlib import Path

# ─── 1) Ensure the project root is on PYTHONPATH ────────────────────────────────
# If you’re in “.../ScoutScheduler/main.py”, we want the parent of
# “ScoutScheduler” (i.e. your repo root) on sys.path, so we can do:
#     import ScoutScheduler.backend.webscraping
#
HERE = Path(__file__).resolve()
PROJECT_ROOT = HERE.parent.parent   # goes from .../ScoutScheduler/main.py → repo root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ─── 2) Pull in both badge & holiday fetchers ─────────────────────────────────
try:
    from ScoutScheduler.backend.webscraping import fetch_badge_data, fetch_school_holidays  # ↵
except ImportError as e:
    print("❗ Could not import one of the scrapers:", e)
    # define no‑ops so main still runs
    def fetch_badge_data(): return {}
    def fetch_school_holidays(): return {}

def initialise_data():
    print("↻ Refreshing badge data…")
    try:
        badges = fetch_badge_data()
        count = len(badges) if hasattr(badges, "__len__") else 0
        print(f"   → Saved {count} badges")
    except Exception as err:
        print("   ! Failed to fetch badges:", err)

    print("↻ Refreshing holiday data…")
    try:
        holidays = fetch_school_holidays()
        count = len(holidays) if hasattr(holidays, "__len__") else 0
        print(f"   → Saved {count} holiday entries")
    except Exception as err:
        print("   ! Failed to fetch holidays:", err)

def main():
    print("▶ Starting Scout Scheduler")
    initialise_data()

    # ─── 3) Launch the GUI ───────────────────────────────────────────────────────
    from ScoutScheduler.gui.scheduler import launch_scheduler
    print("▶ Launching GUI…")
    launch_scheduler()

if __name__ == "__main__":
    main()
