"""
Schedule generator that calls Writer once and converts its reply to calendar events.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

from .writer_client import WriterAPIError, get_completion
from .data_store import save_events

Event = Dict[str, Any]


def generate_schedule(
    start: date, end: date, *, topics: List[str] | None = None
) -> List[Event]:
    prompt = (
        f"Create a scout meeting plan between {start} and {end}. "
        f"Focus topics: {', '.join(topics) if topics else 'general skills'}."
    )

    try:
        text = get_completion(prompt)
    except WriterAPIError as exc:
        # graceful degradation – return stub event only
        text = f"(AI unavailable: {exc})"

    event: Event = {
        "date": start.isoformat(),  # datetime docs – isoformat() is portable :contentReference[oaicite:4]{index=4}
        "title": "AI-Suggested Session",
        "description": text.strip(),
    }

    # Persist alongside existing list
    existing = load_events()
    existing.append(event)
    save_events(existing)
    return [event]


def load_events() -> List[Event]:  # thin wrapper to keep import order flat
    from .data_store import load_events as _ld

    return _ld()
