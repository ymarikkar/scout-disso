import os
import json
from typing import List, Dict, Union

# Paths for badge catalogue and user progress
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
BADGE_FILE = os.path.join(DATA_DIR, "badge_data.json")
USER_FILE  = os.path.join(DATA_DIR, "user_badges.json")


def _load_json(path: str) -> Dict:
    """
    Load JSON data from the given file path. Returns an empty dict if file not found.
    Raises RuntimeError if JSON is malformed.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Corrupt JSON file at {path}: {e}")


def _save_json(path: str, data: Dict) -> None:
    """
    Save the given dict to the specified JSON file, creating directories if needed.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, path)


def get_all_badges() -> List[str]:
    """
    Return a sorted list of all badge names from the badge catalogue.
    """
    badges = _load_json(BADGE_FILE)
    return sorted(badges.keys())


def get_completed_badges(user_id: str = "default") -> List[str]:
    """
    Return a list of badge names that the specified user has completed.
    """
    data = _load_json(USER_FILE)
    completed = data.get(user_id)
    return list(completed) if isinstance(completed, list) else []


def get_pending_badges(user_id: str = "default") -> List[str]:
    """
    Return a list of badge names that the user has not yet completed.
    """
    all_badges = set(get_all_badges())
    completed  = set(get_completed_badges(user_id))
    pending    = all_badges - completed
    return sorted(pending)


def mark_badge_completed(badge_name: str, user_id: str = "default") -> None:
    """
    Mark the specified badge as completed for the given user.
    Raises ValueError if the badge is not in the master list.
    """
    all_badges = get_all_badges()
    if badge_name not in all_badges:
        raise ValueError(f"Badge '{badge_name}' not found in catalogue.")

    data = _load_json(USER_FILE)
    user_list = data.get(user_id, [])
    if badge_name in user_list:
        return  # already marked

    user_list.append(badge_name)
    data[user_id] = user_list
    _save_json(USER_FILE, data)


def reset_user_progress(user_id: str = "default") -> None:
    """
    Clear all completed badges for the specified user.
    """
    data = _load_json(USER_FILE)
    if user_id in data:
        data[user_id] = []
        _save_json(USER_FILE, data)


def update_badge_stage(badge_name: str,
                       stage: int,
                       max_stage: int = 1,
                       user_id: str = "default") -> None:
    """
    Set the user's badge stage for multi-stage badges.
    When stage >= max_stage, the badge is considered fully completed.
    """
    data = _load_json(USER_FILE)
    user_data = data.get(user_id)

    # Migrate flat list to dict of stages if needed
    if user_data is None:
        user_data = {}
    elif isinstance(user_data, list):
        user_data = {b: max_stage for b in user_data}

    # Update stage
    user_data[badge_name] = min(stage, max_stage)
    data[user_id] = user_data
    _save_json(USER_FILE, data)


def get_badge_stage(badge_name: str, user_id: str = "default") -> Union[int, None]:
    """
    Return the current stage of a multi-stage badge for the user,
    or None if not started.
    """
    data = _load_json(USER_FILE)
    user_data = data.get(user_id)
    if isinstance(user_data, dict):
        return user_data.get(badge_name)
    return None
