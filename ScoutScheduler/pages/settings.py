# pages/settings.py
"""
Settings & Data – export/import JSON and refresh web data.
"""
import json

import streamlit as st
from backend.data_store import (load_badges, load_events, save_badges,
                                save_events)
from backend.webscraper import \
    refresh_harrow_holidays  # note the trailing "ing"

st.title("⚙️ Settings & Data")

# ---------------------------------------------------------------- #
# Export / import
# ---------------------------------------------------------------- #
left, right = st.columns(2)

with left:
    st.header("Export / import events")

    st.download_button(
        "⬇️ Download events JSON",
        data=json.dumps(load_events(), indent=2),
        file_name="events.json",
        mime="application/json",
    )

    uploaded = st.file_uploader("⬆️ Upload events JSON", type="json")
    if uploaded and st.button("Replace events"):
        ev = json.load(uploaded)
        save_events(ev)
        st.session_state.events = ev
        st.success("Events replaced! Go to the Calendar page to verify.")

with right:
    st.header("Export / import badges")

    st.download_button(
        "⬇️ Download badges JSON",
        data=json.dumps(load_badges(), indent=2),
        file_name="badges.json",
        mime="application/json",
    )

    uploaded_b = st.file_uploader("⬆️ Upload badges JSON", type="json", key="b_up")
    if uploaded_b and st.button("Replace badges"):
        bd = json.load(uploaded_b)
        save_badges(bd)
        st.session_state.badges = bd
        st.success("Badges replaced! Go to the Badges page to verify.")

# ---------------------------------------------------------------- #
# Refresh from the web
# ---------------------------------------------------------------- #
st.divider()
st.subheader("Refresh data from the web")

col_hol, col_badge = st.columns(2)

with col_hol:
    if st.button("🔄 Refresh Harrow holidays"):
        try:
            count = len(refresh_harrow_holidays())
            st.success(f"Fetched {count} holiday periods.")
        except Exception as e:
            st.error(f"Failed to fetch holidays: {e}")

with col_badge:
    if st.button("🔄 Refresh badge catalogue"):
        try:
            count = len(refresh_badge_catalogue())
            # reload in-memory state so sidebar/pages pick it up next render
            st.session_state.badges = load_badges()
            st.success(f"Fetched {count} badges. Go to the Badges page to see them.")
        except Exception as e:
            st.error(f"Failed to fetch badges: {e}")
