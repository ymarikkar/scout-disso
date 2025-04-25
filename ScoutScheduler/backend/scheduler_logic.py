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
from dotenv import load_dotenv
load_dotenv()   # picks up .env variables

import requests, os, json, hashlib
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from cachetools import TTLCache
from typing import List, Dict, Any

# Re-usable session with back-off
_session = requests.Session()
retry = Retry(
    total=3,                 # 3 attempts
    backoff_factor=1.5,      # 0s, 1.5s, 3s delays
    status_forcelist=[502, 503, 504],
    allowed_methods=["POST"],
)
_session.mount("https://", HTTPAdapter(max_retries=retry))



# ─── Writer API config ─────────────────────────────────────────────────────
CHAT_URL   = "https://api.writer.com/v1/chat/completions"
COMP_URL   = "https://api.writer.com/v1/completions"
MODEL      = os.getenv("WRITER_MODEL", "palmyra-chat")
API_KEY    = os.getenv("WRITER_API_KEY")
CACHE      = TTLCache(maxsize=100, ttl=600)

# shared retrying session (60-second timeout)
session = requests.Session()
session.mount("https://", HTTPAdapter(
    max_retries=Retry(total=3, backoff_factor=1.5,
                      status_forcelist=[502,503,504]))
)

# ─── in-memory 10-minute cache ─────────────────────────────────────────────
_CACHE: TTLCache = TTLCache(maxsize=100, ttl=600)

# ─── Call Writer (chat) ────────────────────────────────────────────────────
def _call_writer_chat(prompt: str) -> str:
    if not WRITER_KEY:
        raise RuntimeError("WRITER_API_KEY is not set")

    body = {
        "model": WRITER_MODEL,
        "messages": [
            {"role": "system", "content": "Return ONLY valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "n": 1,
    }

    resp = _session.post(
        WRITER_CHAT_URL,
        headers={"Authorization": f"Bearer {WRITER_KEY}",
                 "Content-Type": "application/json"},
        json=body,
        timeout=60,
    )
    if resp.status_code == 401:
        raise RuntimeError("Writer 401 – bad API key")
    resp.raise_for_status()

    # ---------- tolerant parsing ----------
    try:
        data = resp.json()
    except ValueError:
        # non-JSON body
        return resp.text.strip()

    # 1) OpenAI-style
    if "choices" in data:
        choice = data["choices"][0]
        if "message" in choice:
            return choice["message"]["content"]
        if "text" in choice:
            return choice["text"]

    # 2) Some Writer plans
    if "content" in data:
        return data["content"]
    if "data" in data and isinstance(data["data"], list):
        return data["data"][0].get("text") or data["data"][0].get("content", "")

    # 3) Unknown format
    raise RuntimeError(f"Unexpected Writer response: {data}")

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
