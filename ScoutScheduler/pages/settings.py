# pages/settings.py
"""
Settings & Data page – export / import JSON and refresh data from the web.
"""

import json
import streamlit as st
from backend.data_store import (
    load_events, save_events,
    load_badges, save_badges,
)
from backend.webscraper import (
    refresh_harrow_holidays,
    refresh_badge_catalogue,
)

st.title("⚙️ Settings & Data")

# -------------------------------------------------------------------- #
# Export / import sections
# -------------------------------------------------------------------- #
left, right = st.columns(2)

# ---------- Events --------------------------------------------------- #
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
        events = json.load(uploaded)
        save_events(events)
        st.session_state.events = events
        st.success("Events replaced. Refresh Calendar page.")

# ---------- Badges --------------------------------------------------- #
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
        badges = json.load(uploaded_b)
        save_badges(badges)
        st.session_state.badges = badges
        st.success("Badges replaced. Refresh Badges page.")

# -------------------------------------------------------------------- #
# Refresh from the web
# -------------------------------------------------------------------- #
st.divider()
st.subheader("Refresh data from the web")

col_holidays, col_badges = st.columns(2)

with col_holidays:
    if st.button("🔄 Refresh Harrow holidays"):
        try:
            n = len(refresh_harrow_holidays())
            st.success(f"Fetched {n} holiday periods")
        except Exception as e:
            st.error(f"Failed: {e}")

with col_badges:
    if st.button("🔄 Refresh badge catalogue"):
        try:
            n = len(refresh_badge_catalogue())
            st.session_state.badges = load_badges()
            st.success(f"Fetched {n} badges")
            st.experimental_rerun()           # reload pages & sidebar
        except Exception as e:
            st.error(f"Failed: {e}")
