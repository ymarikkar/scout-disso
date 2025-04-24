import sys, os

# Ensure the parent folder (ScoutScheduler/) is on Python's module path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
from backend import badge_logic

from backend.data_store import load_badges

st.title("🎖️ Badge Manager")

badges = load_badges()

for name, info in badges.items():
    with st.expander(f"{name}  —  {info['status']} ({info['completion']}%)"):
        st.markdown(f"**Sessions required:** {info['sessions']}")
        st.markdown(f"**Section:** {info.get('section', '—')}")
        st.markdown(f"**Description:** {info['description'] or 'No description'}")
        if info["requirements"]:
            st.markdown("**Requirements:**")
            for req in info["requirements"]:
                st.markdown(f"- {req}")
        st.divider()