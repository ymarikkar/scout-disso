"""
ScoutScheduler ── AI Scheduler Logic
===================================
Generates badge-session date suggestions with Writer’s API.
"""

from __future__ import annotations
import os, json, hashlib
from typing import List, Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from cachetools import TTLCache

from .data_store import save_events

# ─────────────────────────────────────────────────────────────────────────────
# Writer configuration
# ─────────────────────────────────────────────────────────────────────────────
API_KEY        = os.getenv("WRITER_API_KEY")        # set this in env or .env
CHAT_MODEL     = os.getenv("WRITER_MODEL", "palmyra-chat")
BASE_MODEL     = CHAT_MODEL.replace("-chat", "-base")  # fallback model

CHAT_URL       = "https://api.writer.com/v1/chat/completions"
COMP_URL       = "https://api.writer.com/v1/completions"

# ─────────────────────────────────────────────────────────────────────────────
# Retryable HTTP session (3 tries, 1.5-s back-off)
# ─────────────────────────────────────────────────────────────────────────────
_session = requests.Session()
_session.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=3,
            backoff_factor=1.5,
            status_forcelist=[502, 503, 504],
            allowed_methods=["POST"],
        )
    ),
)

# ─────────────────────────────────────────────────────────────────────────────
# In-memory 10-minute cache
# ─────────────────────────────────────────────────────────────────────────────
_CACHE: TTLCache = TTLCache(maxsize=100, ttl=600)


# ─────────────────────────────────────────────────────────────────────────────
# Writer helpers
# ─────────────────────────────────────────────────────────────────────────────
def _writer_chat(prompt: str) -> str:
    """Primary call – chat endpoint with strict JSON response."""
    body = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": "Return ONLY valid JSON."},
            {"role": "user",   "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "n": 1,
    }
    r = _session.post(
        CHAT_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json=body,
        timeout=60,
    )
    if r.status_code == 400:
        raise requests.HTTPError(r.text, response=r)
    if r.status_code == 401:
        raise RuntimeError("Writer 401 – invalid API key")
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

    if r.status_code >= 500:
    raise RuntimeError(
        "Writer API is temporarily unavailable (5xx). "
        "Please wait a few minutes and try again."
    )



def _writer_comp(prompt: str) -> str:
    """Fallback – Writer /v1/completions with JSON output."""
    body = {
        "model": BASE_MODEL,      # e.g. palmyra-base
        "prompt": prompt,         # ← required field
        "n": 1,                   # one completion
        "output_format": "json",  # force JSON
    }

    r = _session.post(
        COMP_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=60,
    )
    if r.status_code == 400:
        raise RuntimeError(f"Writer 400 (completions): {r.text}")
    r.raise_for_status()

    data = r.json()
    if "choices" in data:
        return data["choices"][0].get("text") or data["choices"][0].get("content", "")
    return data.get("content", "")

    if r.status_code >= 500:
        raise RuntimeError(
            "Writer API is temporarily unavailable (5xx). "
            "Please wait a few minutes and try again."
        )




def _call_writer(prompt: str) -> str:
    """Chat first; on 400 fall back to completions."""
    if not API_KEY:
        raise RuntimeError("WRITER_API_KEY is not set in your environment.")
    try:
        return _writer_chat(prompt)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 400:
            # print body for debug
            print("Writer chat 400 body →", e.response.text[:250])
            return _writer_comp(prompt)
        raise RuntimeError(f"Writer error: {e}") from None
    except requests.Timeout:
        raise RuntimeError("Writer API timed out; please try again.") from None


# ─────────────────────────────────────────────────────────────────────────────
# Prompt builder
# ─────────────────────────────────────────────────────────────────────────────
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
  {{"badge":"Badge Name","date":"YYYY-MM-DD"}}
]
"""


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def generate_schedule(
    events: List[Dict[str, Any]],
    badges: Dict[str, Dict[str, Any]],
    holidays: List[Dict[str, Any]],
    prefs: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Return list of {"badge","date"} suggestions (uses cache, raises RuntimeError on failure).
    """
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
    raw = _call_writer(prompt)

    try:
        suggestions = json.loads(raw)
    except json.JSONDecodeError:
        # attempt to pull JSON array from raw text
        import re
        m = re.search(r"\[.*\]", raw, re.S)
        if not m:
            raise RuntimeError("Writer returned non-JSON suggestions:\n" + raw)
        suggestions = json.loads(m.group(0))

    _CACHE[cache_key] = suggestions
    return suggestions


def add_suggestion(events: List[Dict[str, Any]], suggestion: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Append a suggestion to events list and persist to disk.
    """
    events.append(
        {"date": suggestion["date"], "title": suggestion["badge"], "description": ""}
    )
    save_events(events)
    return events
