import sys, os

# Ensure the parent folder (ScoutScheduler/) is on Python's module path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# pages/calendar.py

import streamlit as st
from streamlit_calendar import calendar
from datetime import date
from dateutil.parser import parse as parse_date

from backend.data_store import load_events, save_events, load_holidays

# ─── SESSION-STATE BOOTSTRAP ──────────────────────────────────────────────
if "events" not in st.session_state:
    st.session_state.events = load_events()

# ─── PAGE TITLE ────────────────────────────────────────────────────────────
st.title("📅 Calendar")

# ─── BUILD EVENT FEED ──────────────────────────────────────────────────────
cal_events = [
    {
        "title": ev["title"],
        "start": ev["date"],
        "extendedProps": {"description": ev["description"]},
        "backgroundColor": "#3B82F6",  # blue for user events
    }
    for ev in st.session_state.events
]

# ─── HOLIDAY OVERLAY ───────────────────────────────────────────────────────
for hol in load_holidays():
    cal_events.append(
        {
            "title": hol["name"],
            "start": hol["start"],
            "end": hol["end"],
            "backgroundColor": "#EC4899",  # pink
            "borderColor": "#EC4899",
            "display": "background",
        }
    )

# ─── RENDER CALENDAR ───────────────────────────────────────────────────────
selected = calendar(
    events=cal_events,
    options={
        "initialView": "dayGridMonth",
        "selectable": True,
        "height": 650,
    },
    custom_css=".fc {font-size:0.9rem;}",
)

# ─── CLICK HANDLERS ─────────────────────────────────────────────────────────
if selected and selected.get("event"):
    ev = selected["event"]
    st.info(f"**{ev['title']}**  \n{ev['extendedProps'].get('description','')}")
elif selected and selected.get("start"):
    chosen = parse_date(selected["start"]).date()
    with st.form("add_event"):
        title = st.text_input("Event title")
        desc = st.text_area("Description")
        if st.form_submit_button("Add"):
            st.session_state.events.append(
                {"date": chosen.isoformat(), "title": title, "description": desc}
            )
            save_events(st.session_state.events)
            st.experimental_rerun()
