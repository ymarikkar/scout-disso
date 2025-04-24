# streamlit_app.py
# --------------------------------------------------------------------------- #
# Scout-Disso – Streamlit front-end
# --------------------------------------------------------------------------- #
 # streamlit_app.py
# streamlit_app.py (top of file)
import sys, os

# Ensure this file’s folder (ScoutScheduler/) is on Python’s search path
HERE = os.path.dirname(__file__)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


-import streamlit as st
+import sys
+import os
+import streamlit as st
 from datetime import date
 from backend import scheduler_logic

from datetime import date
from backend import scheduler_logic
from backend.data_store import (
    load_events,       # NEW unified helpers
    save_events,
    load_badges,
    save_badges,
)

st.set_page_config(
    page_title="Scout Leader Scheduler",
    page_icon="🧭",
    layout="wide",
)

# -------------------------- session bootstrap ------------------------------ #
if "events" not in st.session_state:
    st.session_state.events = load_events()        # was load_generated()
if "badges" not in st.session_state:
    st.session_state.badges = load_badges()

st.sidebar.title("Scout Leader Scheduler")
st.sidebar.success("Use the ▶ icons above to navigate.")

# -------------------------- sidebar button --------------------------------- #
if st.sidebar.button("Generate AI Schedule"):
    today = date.today()
    new_events = scheduler_logic.generate_schedule(today, today)
    st.session_state.events.extend(new_events)
    save_events(st.session_state.events)            # was save_generated()
    st.sidebar.success("AI suggestions saved! Refresh Calendar page.")

# --------------------------- routing (multipage) --------------------------- #
# Streamlit automatically picks up files in /pages; nothing else needed here.
st.write(
    """
    ### Welcome  
    Use the left-hand navigation to open **Dashboard**, **Badges**, or **Calendar**.
    """
)
