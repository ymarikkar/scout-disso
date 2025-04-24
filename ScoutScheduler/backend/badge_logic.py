"""
Simple persistence helpers for scout badges.
"""
from __future__ import annotations

import json
import os
import typing as _t

_BADGE_FILE = os.path.join(os.path.dirname(__file__), "badges.json")
Badge = dict[str, _t.Any]

# --------------------------------------------------------------------------- #
# Low-level persistence
# --------------------------------------------------------------------------- #

def _read() -> dict[str, Badge]:
    if not os.path.exists(_BADGE_FILE):
        return {}
    with open(_BADGE_FILE, encoding="utf-8") as fh:
        return _t.cast(dict[str, Badge], json.load(fh))

def _write(data: dict[str, Badge]) -> None:
    with open(_BADGE_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)

# --------------------------------------------------------------------------- #
# Public helpers used by GUI
# --------------------------------------------------------------------------- #

def get_all_badges() -> dict[str, Badge]:
    return _read()

def get_completed_badges() -> list[Badge]:
    return [
        b for b in _read().values()
        if b.get("status") == "Completed"
    ]

def mark_badge_completed(name: str) -> bool:
    badges = _read()
    if name not in badges:
        return False
    badges[name]["status"] = "Completed"
    badges[name]["completion"] = 100
    _write(badges)
    return True

def mark_badge_incomplete(name: str) -> bool:
    """
    **NEW** helper required by `gui/badge_tracker.py`.

    Resets a badge to “Not Started” and 0 % completion.
    Returns True if the badge existed, False otherwise.
    """
    badges = _read()
    if name not in badges:
        return False
    badges[name]["status"] = "Not Started"
    badges[name]["completion"] = 0
    _write(badges)
    return True
