import streamlit as st
from backend import badge_logic

st.title("🎖️ Badge Manager")

# ----- Badge table -----------------------------------------------------------
st.dataframe(st.session_state.badges, use_container_width=True)

# ----- Add / edit / delete ---------------------------------------------------
with st.expander("➕ Add a new badge"):
    name = st.text_input("Badge name")
    sessions = st.number_input("Sessions required", 1, 20, 1)
    description = st.text_area("Description")
    requirements = st.text_area("Requirements (one per line)")
    if st.button("Save badge"):
        st.session_state.badges[name] = {
            "name": name,
            "sessions": sessions,
            "status": "Not Started",
            "completion": 0,
            "description": description,
            "requirements": [r.strip() for r in requirements.splitlines() if r],
        }
        badge_logic._write(st.session_state.badges)
        st.rerun()

# Simple inline delete
to_delete = st.selectbox("Select badge to delete", [""] + list(st.session_state.badges))
if to_delete and st.button("Delete selected badge"):
    st.session_state.badges.pop(to_delete, None)
    badge_logic._write(st.session_state.badges)
    st.rerun()
