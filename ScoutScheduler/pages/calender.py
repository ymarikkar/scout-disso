import streamlit as st
from streamlit_calendar import calendar
from datetime import date
from dateutil.parser import parse as parse_date

from backend.data_store import load_holidays
# events already live in st.session_state.events (set in streamlit_app.py)

st.title("📅 Calendar")

# ------------------------- build event feed ------------------------------- #
cal_events = [
    {
        "title": ev["title"],
        "start": ev["date"],
        "extendedProps": {"description": ev["description"]},
        "backgroundColor": "#3B82F6",          # blue for events
    }
    for ev in st.session_state.events
]

# ----- add holiday overlay (pink) ---------------------------------------- #
for hol in load_holidays():
    cal_events.append(
        {
            "title": hol["name"],
            "start": hol["start"],
            "end": hol["end"],
            "backgroundColor": "#EC4899",      # pink for holidays
            "borderColor": "#EC4899",
            "display": "background",           # coloured bar behind days
        }
    )

# --------------------------- calendar widget ----------------------------- #
selected = calendar(
    events=cal_events,
    options={
        "initialView": "dayGridMonth",
        "selectable": True,
        "height": 650,
    },
    custom_css=".fc {font-size:0.9rem;}",
)

# --------------------------- click handlers ------------------------------ #
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
            from backend.data_store import save_events

            save_events(st.session_state.events)
            st.experimental_rerun()
