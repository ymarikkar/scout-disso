from pathlib import Path
import json
from typing import List, Dict
from .data_models import Badge, Session, Preferences

DATA_DIR      = Path("data")
BADGE_FILE    = DATA_DIR / "badge_data.json"
HOLIDAY_FILE  = DATA_DIR / "holiday_data.json"
SESSION_FILE  = DATA_DIR / "sessions.json"

def load_badges() -> Dict[str, str]:
    if not BADGE_FILE.exists():
        return {}
    return json.loads(BADGE_FILE.read_text(encoding="utf-8"))

def save_badges(badges: Dict[str, str]):
    DATA_DIR.mkdir(exist_ok=True)
    BADGE_FILE.write_text(json.dumps(badges, indent=2), encoding="utf-8")

def load_holidays() -> Dict[str, Dict[str, List[str]]]:
    if not HOLIDAY_FILE.exists():
        return {}
    return json.loads(HOLIDAY_FILE.read_text(encoding="utf-8"))

def save_holidays(holidays: Dict[str, Dict[str, List[str]]]):
    DATA_DIR.mkdir(exist_ok=True)
    HOLIDAY_FILE.write_text(json.dumps(holidays, indent=2), encoding="utf-8")

def load_sessions() -> List[str]:
    if not SESSION_FILE.exists():
        return []
    return json.loads(SESSION_FILE.read_text(encoding="utf-8"))

def save_sessions(sessions: List[str]):
    DATA_DIR.mkdir(exist_ok=True)
    SESSION_FILE.write_text(json.dumps(sessions, indent=2), encoding="utf-8")
