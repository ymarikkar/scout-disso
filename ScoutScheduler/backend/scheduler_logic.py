"""
Back-end helpers for schedule generation and external API calls.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import typing as _t

import requests

# --------------------------------------------------------------------------- #
# Writer-completions helper
# --------------------------------------------------------------------------- #

_WRITER_URL = "https://api.writer.com/v1/completions"
# Keep the key outside source; read from env var or a .env loader.
_API_KEY = os.getenv("WRITER_API_KEY", "")

class WriterAPIError(RuntimeError):
    """Raised when the Writer call fails and we want to bubble it up to the UI."""

def _call_writer(prompt: str, *, model: str = "palmyra-base") -> str:
    """
    Send `prompt` to Writer; return the first completion text or raise
    WriterAPIError. Wrapped in a function so that *importing* the module never
    performs HTTP. 400/500 responses are caught and re-raised as WriterAPIError.
    """
    headers = {
        "Authorization": f"Bearer {_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "inputs": prompt,
        "n": 1,
    }

    try:
        r = requests.post(_WRITER_URL, headers=headers, json=payload, timeout=30)
        r.raise_for_status()  # 4xx / 5xx ➜ HTTPError
    except requests.exceptions.HTTPError as exc:
        raise WriterAPIError(f"Writer API error: {exc}") from exc
    except requests.exceptions.RequestException as exc:
        raise WriterAPIError(f"Writer API transport error: {exc}") from exc

    data = r.json()
    # Shape: {"choices":[{"text":"…"}], …}
    try:
        return data["choices"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise WriterAPIError("Unexpected Writer payload") from exc

# --------------------------------------------------------------------------- #
# Public interface consumed by gui/scheduler.py
# --------------------------------------------------------------------------- #

ScheduleEvent = dict[str, _t.Any]  # very light alias

def generate_schedule(
    start_date: _dt.date,
    end_date: _dt.date,
    *,
    topics: list[str] | None = None,
) -> list[ScheduleEvent]:
    """
    High-level helper called from the GUI ― you can extend this later.

    For now, it calls Writer once with a templated prompt and produces a
    single demo event so the calendar can paint something.
    """
    prompt_parts = [
        "Create a detailed scout meeting plan.",
        f"Start date: {start_date.isoformat()}",
        f"End date: {end_date.isoformat()}",
    ]
    if topics:
        prompt_parts.append(f"Focus topics: {', '.join(topics)}")
    prompt = "\n".join(prompt_parts)

    try:
        text = _call_writer(prompt)
    except WriterAPIError as err:
        # Fallback: keep the app alive but return an empty list
        print("⚠️  Writer call failed:", err)
        text = "Free-form activities"

    # Simple demo output: first session on the start date
    return [
        {
            "date": start_date.isoformat(),
            "title": "AI-Suggested Session",
            "description": text.strip(),
        }
    ]

# --------------------------------------------------------------------------- #
# Utility: save & load generated schedules
# --------------------------------------------------------------------------- #

_SCHEDULE_PATH = os.path.join(os.path.dirname(__file__), "generated_schedule.json")

def save_generated(schedule: list[ScheduleEvent]) -> None:
    with open(_SCHEDULE_PATH, "w", encoding="utf-8") as fh:
        json.dump(schedule, fh, indent=2)

def load_generated() -> list[ScheduleEvent]:
    if not os.path.exists(_SCHEDULE_PATH):
        return []
    with open(_SCHEDULE_PATH, encoding="utf-8") as fh:
        return _t.cast(list[ScheduleEvent], json.load(fh))
