#!/usr/bin/env python3
"""
Wrapper that finds and launches the Streamlit front-end.

Why v2?
  • v1 assumed streamlit_app.py lives *one* directory above this file.
  • If you saved it inside the package (ScoutScheduler/streamlit_app.py) or
    somewhere else, Streamlit couldn’t find it and raised
      “Error: Invalid value: File does not exist …”  (same symptom described
      in the Streamlit forums).                     # :contentReference[oaicite:0]{index=0}

This version:
  1. Looks for streamlit_app.py next to this file *and* one level up.
  2. Falls back to an environment variable if you prefer a custom path.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

CANDIDATES = [
    Path(__file__).resolve().parent / "streamlit_app.py",       # package-local
    Path(__file__).resolve().parents[1] / "streamlit_app.py",   # repo root
]

# Allow power users to override with an env-var
env_override = os.getenv("SCOUT_STREAMLIT_APP")
if env_override:
    CANDIDATES.insert(0, Path(env_override).expanduser().resolve())

# Pick the first existing file
try:
    APP_FILE = next(p for p in CANDIDATES if p.exists())
except StopIteration:
    print("❌  streamlit_app.py not found in any expected location:")
    for p in CANDIDATES:
        print("   •", p)
    print("\nSet SCOUT_STREAMLIT_APP or move the file accordingly.")
    sys.exit(1)

def main() -> None:
    print("🚀  Opening Scout-Disso Streamlit UI …")
    # `check=False` avoids bubbling Streamlit’s Ctrl-C up as CalledProcessError
    subprocess.run(["streamlit", "run", str(APP_FILE)], check=False)

if __name__ == "__main__":
    main()
