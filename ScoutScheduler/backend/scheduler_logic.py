"""
ScoutScheduler ── AI Scheduler Logic
===================================
Uses Writer Chat-Completion API to create badge-session date suggestions.
"""

from __future__ import annotations
import os, json, hashlib
from typing import List, Dict, Any
import requests
from cachetools import TTLCache

from .data_store import save_events

# ─── Writer API config ─────────────────────────────────────────────────────
WRITER_CHAT_URL   = "https://api.writer.com/v1/chat/completions"
WRITER_MODEL      = os.getenv("WRITER_MODEL", "palmyra-chat")  # chat-enabled model
WRITER_KEY        = os.getenv("WRITER_API_KEY")                # must be exported

# ─── in-memory 10-minute cache ─────────────────────────────────────────────
_CACHE: TTLCache = TTLCache(maxsize=100, ttl=600)

# ─── Call Writer (chat) ────────────────────────────────────────────────────
def _call_writer_chat(prompt: str) -> str:
    if not WRITER_KEY:
        raise RuntimeError("WRITER_API_KEY is not set in your environment.")

    headers = {
        "Authorization": f"Bearer {WRITER_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": WRITER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are an assistant that ONLY returns valid JSON arrays.",
            },
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},   # force JSON
        "n": 1,
    }

    resp = requests.post(WRITER_CHAT_URL, headers=headers, json=body, timeout=30)
    if resp.status_code == 401:
        raise RuntimeError("Writer API 401 – invalid API key")
    if resp.status_code >= 500:
        raise RuntimeError("Writer API is unavailable (5xx)")

    data = resp.json()
    return data["choices"][0]["message"]["content"]

# ─── Prompt builder ────────────────────────────────────────────────────────
def _build_prompt(events, holidays, badge_needs, prefs) -> str:
    return f"""
Existing events: {[e['date'] for e in events]}
School holidays: {[ (h['start'], h['end']) for h in holidays ]}

Badge sessions needed:
{json.dumps(badge_needs, indent=2)}

Preferences:
  • weekend_only: {prefs['weekend_only']}
  • time_of_day:  {prefs['time_of_day']}

For each badge, output exactly sessions_left dates within the next 30 days
that do NOT clash with events or holidays and respect preferences.
Return ONLY valid JSON in this form:

[
  {{"badge":"Badge Name","date":"YYYY-MM-DD"}},
  …
]
"""

# ─── Public functions ──────────────────────────────────────────────────────
def generate_schedule(
    events: List[Dict[str, Any]],
    badges: Dict[str, Dict[str, Any]],
    holidays: List[Dict[str, Any]],
    prefs: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Return list of {{badge,date}} suggestions (cached)."""

    badge_needs = [
        {
            "name": n,
            "sessions_left": max(1, round((100 - b["completion"]) / 100 * b["sessions"])),
        }
        for n, b in badges.items()
        if b["status"] != "Completed"
    ]
    if not badge_needs:
        return []

    key_material = {
        "events": sorted(e["date"] for e in events),
        "holidays": sorted(f"{h['start']}_{h['end']}" for h in holidays),
        "badge_needs": badge_needs,
        "prefs": prefs,
    }
    cache_key = hashlib.sha256(json.dumps(key_material, sort_keys=True).encode()).hexdigest()
    if (cached := _CACHE.get(cache_key)):
        return cached

    prompt = _build_prompt(events, holidays, badge_needs, prefs)
    raw_json = _call_writer_chat(prompt)

    try:
        suggestions = json.loads(raw_json)
    except json.JSONDecodeError:
        raise RuntimeError("Writer returned non-JSON suggestions:\n" + raw_json)

    _CACHE[cache_key] = suggestions
    return suggestions

def add_suggestion(events: List[Dict[str, Any]], suggestion: Dict[str, str]) -> List[Dict[str, Any]]:
    """Append suggestion to events list and persist to disk."""
    events.append(
        {"date": suggestion["date"], "title": suggestion["badge"], "description": ""}
    )
    save_events(events)
    return events
