#!/usr/bin/env python3
"""
Thin launcher that proxies to the Streamlit UI.

Run either:
    python -m ScoutScheduler.main     # uses this wrapper
or
    streamlit run streamlit_app.py    # calls Streamlit directly
"""
from __future__ import annotations

import subprocess
from pathlib import Path
import sys

# Resolve project root → streamlit_app.py
APP_FILE = Path(__file__).resolve().parents[1] / "streamlit_app.py"


def main() -> None:  # entry-point for `-m ScoutScheduler.main`
    print("🚀 Opening Scout-Disso Streamlit UI…")
    args = ["streamlit", "run", str(APP_FILE)]
    # Use current interpreter’s environment; don’t raise on non-zero exit
    subprocess.run(args, check=False)  # docs.python.org shows check=False keeps wrapper alive :contentReference[oaicite:0]{index=0}


if __name__ == "__main__":
    # Allow `python ScoutScheduler/main.py` too
    sys.exit(main())
