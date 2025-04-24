import sys, os

# Ensure the parent folder (ScoutScheduler/) is on Python's module path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
from datetime import date, timedelta

st.title("🏠 Dashboard")

# Upcoming events -------------------------------------------------------------
st.subheader("Upcoming events (next 30 days)")
today = date.today()
limit = today + timedelta(days=30)
upcoming = [
    ev for ev in st.session_state.events
    if today <= date.fromisoformat(ev["date"]) <= limit
]
if not upcoming:
    st.info("No events planned in the next month.")
else:
    for ev in sorted(upcoming, key=lambda e: e["date"]):
        st.markdown(f"**{ev['date']}** — {ev['title']}  \n{ev['description']}")

# Badges in progress ----------------------------------------------------------
st.subheader("Badges in progress")
in_progress = [
    b for b in st.session_state.badges.values()
    if b.get("status") == "In Progress"
]
if not in_progress:
    st.info("No badges are currently marked *In Progress*.")
else:
    for b in in_progress:
        sessions_left = round((100 - b["completion"]) / 100 * b["sessions"])
        st.write(
            f"**{b['name']}** — {b['completion']} % complete "
            f"({sessions_left} sessions remaining)"
        )
