"""
Unified JSON persistence for badges, events and holidays.

All Streamlit pages should import *only* from this module.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# --------------------------- generic helpers --------------------------- #
def _path(name: str) -> Path:
    return DATA_DIR / f"{name}.json"


def _read(name: str, default: Any) -> Any:
    file = _path(name)
    if not file.exists():
        return default
    with file.open(encoding="utf-8") as fh:
        return json.load(fh)


def _write(name: str, payload: Any) -> None:
    with _path(name).open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)  # pretty print for Git diffs :contentReference[oaicite:3]{index=3}


# ------------------------------ badges --------------------------------- #
def load_badges() -> Dict[str, Dict[str, Any]]:
    return _read("badges", {})


def save_badges(badges: Dict[str, Dict[str, Any]]) -> None:
    _write("badges", badges)


# ------------------------------ events --------------------------------- #
def load_events() -> List[Dict[str, Any]]:
    return _read("events", [])


def save_events(events: List[Dict[str, Any]]) -> None:
    _write("events", events)


# ----------------------------- holidays -------------------------------- #
def load_holidays() -> List[Dict[str, Any]]:
    return _read("holidays", [])


def save_holidays(holidays: List[Dict[str, Any]]) -> None:
    _write("holidays", holidays)
