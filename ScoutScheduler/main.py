#!/usr/bin/env python3
import sys
from pathlib import Path


#!/usr/bin/env python3
"""Thin launcher that proxies to Streamlit."""
import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_FILE = PROJECT_ROOT / "streamlit_app.py"

def main() -> None:
    print("🚀  Opening Scout-Disso Streamlit UI …")
    # Prefer the current Python interpreter’s Streamlit entry-point
    subprocess.run(
        ["streamlit", "run", str(APP_FILE)],
        check=False
    )

if __name__ == "__main__":
    main()
