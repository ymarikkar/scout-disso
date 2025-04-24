"""
ScoutScheduler ── AI Scheduler Logic
===================================

Generates badge–session date suggestions via Writer’s completion API,
with caching and graceful error handling.

Public functions
----------------
generate_schedule(events, badges, holidays, prefs) -> list[dict]
add_suggestion(events, suggestion_dict)            -> list[dict]
"""

from __future__ import annotations
import os, json, hashlib, datetime as dt
import requests
from typing import List, Dict, Any
from cachetools import TTLCache

from .data_store import save_events

# ──────────────────────────── Writer API config ──────────────────────────── #
WRITER_URL = "https://api.writer.com/v1/completions"
WRITER_MODEL = os.getenv("WRITER_MODEL", "palmyra-base")
WRITER_KEY = os.getenv("WRITER_API_KEY")          # must be set in env / .env

# ──────────────────────────────── cache ──────────────────────────────────── #
_CACHE: TTLCache = TTLCache(maxsize=100, ttl=600)   # 10-minute cache


# ────────────────────────────── low-level call ───────────────────────────── #
def _call_writer(prompt: str, model: str = WRITER_MODEL) -> str:
    """Call Writer completion endpoint and return raw text (raises RuntimeError)."""
    if not WRITER_KEY:
        raise RuntimeError("WRITER_API_KEY is not set – define it in your environment")

    headers = {
        "Authorization": f"Bearer {WRITER_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "inputs": prompt,
        "n": 1,  # single completion
    }

    try:
        resp = requests.post(WRITER_URL, headers=headers, json=payload, timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError(f"Network error contacting Writer API: {exc}") from None

    if resp.status_code == 401:
        detail = resp.json().get("message", "Unauthorized")
        raise RuntimeError(f"Writer API 401 – check your API key. Detail: {detail}")
    if resp.status_code >= 500:
        raise RuntimeError("Writer API is currently unavailable (5xx)")

    try:
        return resp.json()["choices"][0]["text"]
    except (KeyError, ValueError) as exc:
        raise RuntimeError(f"Unexpected response format from Writer: {exc}") from None


# ───────────────────────────── prompt builder ────────────────────────────── #
def _build_prompt(
    events: List[Dict[str, Any]],
    holidays: List[Dict[str, Any]],
    badge_needs: List[Dict[str, Any]],
    prefs: Dict[str, Any],
) -> str:
    return f"""
You are an assistant that schedules Scout badge sessions.

Existing events (YYYY-MM-DD):
{[e["date"] for e in events]}

School holidays (no meetings):
{[(h["start"], h["end"]) for h in holidays]}

Badge sessions needed:
{json.dumps(badge_needs, indent=2)}

User preferences:
  • weekend_only: {prefs['weekend_only']}
  • time_of_day:  {prefs['time_of_day']}

Task:
For EACH badge, propose the exact number of sessions_left meeting dates
within the next 30 days, avoiding existing events and holidays, and
respecting preferences.  Output ONLY valid JSON:

[
  {{"badge":"<Badge name>","date":"YYYY-MM-DD"}},
  …
]
"""


# ──────────────────────────── public API ─────────────────────────────────── #
def generate_schedule(
    events: List[Dict[str, Any]],
    badges: Dict[str, Dict[str, Any]],
    holidays: List[Dict[str, Any]],
    prefs: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Return list of {{badge,date}} suggestions (cached).
    May raise RuntimeError with human-readable error for UI.
    """

    # 1) Compute sessions still required per badge
    badge_needs = [
        {
            "name": name,
            "sessions_left": max(
                1,
                round((100 - b["completion"]) / 100 * b["sessions"]),
            ),
        }
        for name, b in badges.items()
        if b["status"] != "Completed"
    ]
    if not badge_needs:
        return []

    # 2) Build cache key
    key_data = {
        "events": sorted(e["date"] for e in events),
        "holidays": sorted(f"{h['start']}_{h['end']}" for h in holidays),
        "badge_needs": badge_needs,
        "prefs": prefs,
    }
    key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    if (cached := _CACHE.get(key)):
        return cached

    # 3) Build prompt and call Writer
    prompt = _build_prompt(events, holidays, badge_needs, prefs)
    raw = _call_writer(prompt)

    # 4) Parse JSON safely
    try:
        suggestions = json.loads(raw)
    except json.JSONDecodeError:
        import re

        m = re.search(r"\[.*\]", raw, re.S)
        if not m:
            raise RuntimeError("Writer returned non-JSON response")
        suggestions = json.loads(m.group(0))

    # 5) Cache & return
    _CACHE[key] = suggestions
    return suggestions


def add_suggestion(
    events: List[Dict[str, Any]],
    suggestion: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Append a suggestion to events list and persist.
    """
    events.append(
        {
            "date": suggestion["date"],
            "title": suggestion["badge"],
            "description": "",
        }
    )
    save_events(events)
    return events
