import streamlit as st
from backend import scheduler_logic, badge_logic

st.title("⚙️ Settings & Data")

col1, col2 = st.columns(2)

with col1:
    st.header("Export / import events")
    if st.download_button(
        "⬇️ Download events JSON",
        scheduler_logic.load_generated(),
        file_name="events.json",
    ):
        st.success("Download started!")
    uploaded = st.file_uploader("⬆️ Upload events JSON", type="json")
    if uploaded and st.button("Replace events"):
        st.session_state.events = scheduler_logic.json.load(uploaded)
        scheduler_logic.save_generated(st.session_state.events)
        st.success("Events replaced.")

with col2:
    st.header("Export / import badges")
    if st.download_button(
        "⬇️ Download badges JSON",
        badge_logic.get_all_badges(),
        file_name="badges.json",
    ):
        st.success("Download started!")
    uploaded_b = st.file_uploader("⬆️ Upload badges JSON", type="json", key="b_up")
    if uploaded_b and st.button("Replace badges"):
        st.session_state.badges = badge_logic.json.load(uploaded_b)
        badge_logic._write(st.session_state.badges)
        st.success("Badges replaced.")
