# ------------------------------------------------------------
# Multipage entry-point.  Run with:  streamlit run streamlit_app.py
# ------------------------------------------------------------
import streamlit as st
from datetime import date
from backend import scheduler_logic

st.set_page_config(
    page_title="Scout Leader Scheduler",
    page_icon="🧭",
    layout="wide",
)

# Global session state bootstrap
if "events" not in st.session_state:
    st.session_state.events = scheduler_logic.load_generated()
if "badges" not in st.session_state:
    from backend import badge_logic
    st.session_state.badges = badge_logic.get_all_badges()

st.sidebar.title("Scout Leader Scheduler")
st.sidebar.success("Use the ▶ icons above to navigate.")

# Simple “Generate AI Schedule” button available on every page
if st.sidebar.button("Generate AI Schedule"):
    today = date.today()
    new_events = scheduler_logic.generate_schedule(today, today)
    st.session_state.events.extend(new_events)
    scheduler_logic.save_generated(st.session_state.events)
    st.sidebar.success("AI suggestions saved! Refresh Calendar page.")
