import json
import os

DATA_FILE = "data/cached_data.json"

def load_sessions():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return []

def save_sessions(sessions):
    with open(DATA_FILE, "w") as file:
        json.dump(sessions, file, indent=4)
