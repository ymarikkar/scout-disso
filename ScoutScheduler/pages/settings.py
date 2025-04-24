# pages/4_⚙️_Settings.py
import json
import streamlit as st
from backend.data_store import (
    load_events,
    save_events,
    load_badges,
    save_badges,
)

st.title("⚙️ Settings & Data")

col1, col2 = st.columns(2)

# --------------------------------------------------------------------------- #
# EVENTS: export / import
# --------------------------------------------------------------------------- #
with col1:
    st.header("Export / import events")

    # Download – convert list → JSON string
    if st.download_button(
        "⬇️ Download events JSON",
        data=json.dumps(load_events(), indent=2),
        file_name="events.json",
        mime="application/json",
    ):
        st.success("Download started!")

    # Upload
    uploaded = st.file_uploader("⬆️ Upload events JSON", type="json")
    if uploaded and st.button("Replace events"):
        new_events = json.load(uploaded)  # list[dict]
        save_events(new_events)
        st.session_state.events = new_events
        st.success("Events replaced. Refresh other pages to see changes.")

# --------------------------------------------------------------------------- #
# BADGES: export / import
# --------------------------------------------------------------------------- #
with col2:
    st.header("Export / import badges")

    if st.download_button(
        "⬇️ Download badges JSON",
        data=json.dumps(load_badges(), indent=2),
        file_name="badges.json",
        mime="application/json",
    ):
        st.success("Download started!")

    uploaded_b = st.file_uploader("⬆️ Upload badges JSON", type="json", key="b_up")
    if uploaded_b and st.button("Replace badges"):
        new_badges = json.load(uploaded_b)  # dict[str, dict]
        save_badges(new_badges)
        st.session_state.badges = new_badges
        st.success("Badges replaced. Refresh other pages to see changes.")
with c2:
    if st.button("🔄 Refresh badge catalogue"):
        count = len(refresh_badge_catalogue())
        st.session_state.badges = load_badges()   # <-- already in patch
        st.experimental_rerun()                   # <— NEW

# --------------------------------------------------------------------------- #
# DATA REFRESH (web scraping) ----------------------------------------------- #
# --------------------------------------------------------------------------- #
from backend.webscraper import refresh_bank_holidays, refresh_badge_catalogue

st.divider()
st.subheader("Refresh data from the web")

c1, c2 = st.columns(2)

with c1:
    if st.button("🔄 Refresh bank-holiday list"):
        count = len(refresh_bank_holidays())
        st.success(f"Fetched {count} holidays from GOV.UK")

with c2:
    if st.button("🔄 Refresh badge catalogue"):
        count = len(refresh_badge_catalogue())
        st.session_state.badges = load_badges()  # update sidebar pages
        st.success(f"Fetched {len(st.session_state.badges)} badges")
