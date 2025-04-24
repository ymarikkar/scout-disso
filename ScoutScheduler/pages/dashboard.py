# pages/dashboard.py
import streamlit as st
from datetime import date

from backend.data_store import load_events, load_badges, load_holidays
from backend.scheduler_logic import generate_schedule, add_suggestion

st.title("📊 Dashboard")

# ------------------ user prefs sidebar ------------------ #
st.sidebar.header("Scheduling Preferences")
pref_weekend = st.sidebar.checkbox("Weekend only", value=False)   # checkbox widget :contentReference[oaicite:4]{index=4}
pref_time    = st.sidebar.selectbox("Preferred time of day", ["any","morning","afternoon"])
prefs = {"weekend_only": pref_weekend, "time_of_day": pref_time}

# ------------------ generate button -------------------- #
if st.button("Generate AI Schedule Suggestions"):
    st.session_state.suggestions = generate_schedule(
        load_events(),
        load_badges(),
        load_holidays(),
        prefs
    )

# ------------------ show suggestions ------------------ #
if "suggestions" in st.session_state:
    st.subheader("AI suggestions")
    if not st.session_state.suggestions:
        st.info("No suggestions returned.")
    for s in st.session_state.suggestions:
        col_badge, col_date, col_add = st.columns([2,1,1])
        col_badge.write(f"**{s['badge']}**")
        col_date.write(s["date"])
        if col_add.button("➕", key=f"add_{s['badge']}_{s['date']}"):
            events = add_suggestion(load_events(), s)
            st.session_state.events = events
            st.success(f"Added {s['badge']} on {s['date']}")
            st.rerun()                                               # st.rerun API :contentReference[oaicite:5]{index=5}
