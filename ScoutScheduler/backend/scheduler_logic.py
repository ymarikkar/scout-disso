# ScoutScheduler/backend/scheduler_logic.py
import os, json, hashlib, datetime as dt
import requests

from .data_store import save_events
from .scheduler_cache import get as cache_get, set as cache_set

WRITER_URL = "https://api.writer.com/v1/completions"           # Writer docs :contentReference[oaicite:1]{index=1}
WRITER_KEY = os.getenv("WRITER_API_KEY")

def _call_writer(prompt: str, model: str = "palmyra-base") -> str:
    """Thin wrapper around Writer completion endpoint."""
    headers = {
        "Authorization": f"Bearer {WRITER_KEY}",                # Bearer auth :contentReference[oaicite:2]{index=2}
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "inputs": prompt,
        "n": 1
    }
    resp = requests.post(WRITER_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["text"]

def _build_prompt(events, holidays, badge_needs, prefs):
    return f"""
You are an assistant that schedules Scout badge sessions.

Existing events: {[e["date"] for e in events]}
School holidays: {[ (h["start"], h["end"]) for h in holidays ]}

Badge sessions needed (JSON):
{json.dumps(badge_needs, indent=2)}

User preferences:
  • weekend_only: {prefs['weekend_only']}
  • time_of_day:  {prefs['time_of_day']}

For EACH badge, propose the exact number of sessions_left meeting
dates within the next 30 days, avoiding any conflicts and
respecting preferences.

Return JSON ONLY:
[
  {{"badge":"<Badge name>","date":"YYYY-MM-DD"}},
  …
]
"""

def generate_schedule(events, badges, holidays, prefs):
    """Return list of {{badge, date}} suggestions (cached)."""
    # ---- badge sessions needed ----
    badge_needs = [
        {
            "name": n,
            "sessions_left": max(1, round((100 - b["completion"]) / 100 * b["sessions"]))
        }
        for n, b in badges.items() if b["status"] != "Completed"
    ]

    # ---- cache key ----
    key_data = {
        "events": sorted(e["date"] for e in events),
        "holidays": sorted(f"{h['start']}_{h['end']}" for h in holidays),
        "badge_needs": badge_needs,
        "prefs": prefs,
    }
    key = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()  # hashlib sha256 :contentReference[oaicite:3]{index=3}
    if (cached := cache_get(key)):
        return cached

    prompt = _build_prompt(events, holidays, badge_needs, prefs)
    raw = _call_writer(prompt)

    # ---- best-effort JSON parse ----
    try:
        suggestions = json.loads(raw)
    except json.JSONDecodeError:
        import re
        m = re.search(r"\[.*\]", raw, re.S)
        suggestions = json.loads(m.group(0)) if m else []

    cache_set(key, suggestions)
    return suggestions

def add_suggestion(events, suggestion):
    """Append suggestion -> events & persist."""
    events.append({
        "date": suggestion["date"],
        "title": suggestion["badge"],
        "description": "",
    })
    save_events(events)
    return events
