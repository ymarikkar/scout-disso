import os
import json
from typing import List, Dict, Union
from writer import Client
from typing import List
from fastapi import FastAPI, HTTPException
from bs4 import BeautifulSoup
import httpx

# initialize once at module level
_writer_client = Client(api_key=os.getenv("WRITER_API_KEY"))
app = FastAPI()

BADGE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "badge_data.json")

# File paths
BADGE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "badge_data.json")
USER_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "user_badges.json")

def load_badges():
    try:
        with open(BADGE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Badge catalogue not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Corrupt badge data")

def _load_json(path: str) -> Dict:
    """
    Load and return JSON data from the given path, or an empty dict if file does not exist.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        raise RuntimeError(f"Corrupt JSON file: {path}")


def _save_json(path: str, data: Dict) -> None:
    """
    Save the given dict data to JSON at the specified path.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_all_badges() -> List[str]:
    """
    Return a sorted list of all badge names from the badge catalogue.
    """
    badges = _load_json(BADGE_FILE)
    return sorted(badges.keys())


def get_completed_badges(user_id: str = "default") -> List[str]:
    """
    Return a list of badge names that the given user has completed.
    """
    data = _load_json(USER_FILE)
    return data.get(user_id, [])


def get_pending_badges(user_id: str = "default") -> List[str]:
    """
    Return a list of badge names that the given user has not yet completed.
    """
    all_badges = set(get_all_badges())
    completed = set(get_completed_badges(user_id))
    pending = all_badges - completed
    return sorted(pending)


def mark_badge_completed(badge_name: str, user_id: str = "default") -> None:
    """
    Mark the specified badge as completed for the given user and save the update.
    Raises ValueError if badge_name does not exist.
    """
    # Validate badge exists
    if badge_name not in get_all_badges():
        raise ValueError(f"Badge '{badge_name}' not found in catalogue.")

    data = _load_json(USER_FILE)
    user_list = data.get(user_id, [])

    if badge_name in user_list:
        return  # Already completed

    user_list.append(badge_name)
    data[user_id] = user_list
    _save_json(USER_FILE, data)


def reset_user_progress(user_id: str = "default") -> None:
    """
    Clear all completed badges for the given user.
    """
    data = _load_json(USER_FILE)
    if user_id in data:
        data[user_id] = []
        _save_json(USER_FILE, data)

# Example advanced function for staged badges (optional)

def update_badge_stage(badge_name: str, stage: int, max_stage: int = 1, user_id: str = "default") -> None:
    """
    Set the user's badge stage for multi-stage badges. When stage >= max_stage, marks badge as completed.
    """
    data = _load_json(USER_FILE)
    user_data = data.get(user_id, {})

    # If storing dict of {badge: stage}
    if isinstance(user_data, dict):
        user_data[badge_name] = min(stage, max_stage)
    else:
        # migrate flat list to dict
        existing = {b: max_stage for b in user_data}
        user_data = existing
        user_data[badge_name] = min(stage, max_stage)

    data[user_id] = user_data
    _save_json(USER_FILE, data)


def get_badge_stage(badge_name: str, user_id: str = "default") -> Union[int, None]:
    """
    Return the current stage of a multi-stage badge for the user, or None if not started.
    """
    data = _load_json(USER_FILE)
    user_data = data.get(user_id, {})
    if isinstance(user_data, dict):
        return user_data.get(badge_name)
    return None
def suggest_next_badges(user_id: str = "default") -> List[str]:
    completed = get_completed_badges(user_id)
    pending   = get_pending_badges(user_id)

    system = (
        "You are ScoutAI, an assistant for Scout leaders. "
        "Given which badges a Cub has completed and which are pending, "
        "recommend the top 3 next badges to pursue, in order of ease and impact."
    )
    user_msg = f"Completed: {completed}\nPending:   {pending}"

    resp = _writer_client.chat.completions.create(
        model="palmyra-x-004",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user_msg}
        ],
        # optional: tool calling could be configured in Studio if you want real-time badge details
    )

    # assume the response is a comma-separated list
    text = resp.choices[0].message.content
    return [b.strip() for b in text.split(",") if b.strip()]
@app.get("/badge_info")
async def badge_info(name: str):
    badges = load_badges()
    url = badges.get(name)
    if not url:
        raise HTTPException(status_code=404, detail="Badge not found")
    # Optionally, scrape description here or return URL only
    return {"name": name, "url": url}

async def fetch_description(url):
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    desc = soup.select_one(".article-content p").get_text(strip=True)
    return desc

@app.get("/badge_info")
async def badge_info(name: str):
    badges = load_badges()
    url = badges.get(name) or raise HTTPException(404)
    desc = await fetch_description(url)
    return {"name": name, "url": url, "description": desc}