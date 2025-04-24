"""
Isolated helper for the Writer AI Studio completions endpoint.
Keeps network I/O out of import-time execution.
"""
from __future__ import annotations

import os
import requests

__all__ = ["get_completion", "WriterAPIError"]

WRITER_URL = "https://api.writer.com/v1/completions"  # official REST guide :contentReference[oaicite:1]{index=1}
API_KEY = os.getenv("WRITER_API_KEY", "")


class WriterAPIError(RuntimeError):
    """Bubble-up transport or 4xx/5xx errors in a single type."""


def get_completion(prompt: str, *, model: str = "palmyra-base") -> str:
    """
    Return the first completion text from Writer.
    Raises WriterAPIError on any problem so callers can fall back gracefully.
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "inputs": prompt, "n": 1}

    try:
        resp = requests.post(WRITER_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["text"]  # shape defined in Writer docs :contentReference[oaicite:2]{index=2}
    except (requests.RequestException, KeyError, IndexError) as exc:
        raise WriterAPIError(str(exc)) from exc
