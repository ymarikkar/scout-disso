import streamlit as st
from streamlit_calendar import calendar
from datetime import date
from dateutil.parser import parse as parse_date

st.title("📅 Calendar")

# Convert internal list-of-dicts to FullCalendar JSON
cal_events = [
    {
        "title": ev["title"],
        "start": ev["date"],
        "extendedProps": {"description": ev["description"]},
    }
    for ev in st.session_state.events
]

selected = calendar(
    events=cal_events,
    options={"initialView": "dayGridMonth", "selectable": True},
    custom_css=""" .fc {font-size: 0.9rem;} """,
)

# selected is a dict with click info
if selected and selected.get("event"):
    ev = selected["event"]
    st.info(f"**{ev['title']}**  \n{ev['extendedProps']['description']}")
elif selected and selected.get("start"):
    # User clicked an empty date → quick-add event
    chosen = parse_date(selected["start"]).date()
    with st.form("add_event"):
        title = st.text_input("Event title")
        desc = st.text_area("Description")
        submitted = st.form_submit_button("Add")
        if submitted:
            st.session_state.events.append(
                {"date": chosen.isoformat(), "title": title, "description": desc}
            )
            from backend import scheduler_logic
            scheduler_logic.save_generated(st.session_state.events)
            st.experimental_rerun()
