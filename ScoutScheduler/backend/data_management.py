import json
import os


DATA_FILE = "data/cached_data.json"

# backend/data_management.py
def load_sessions():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE) as f:
        return json.load(f)

def save_sessions(lst):
    with open(DATA_FILE, "w") as f:
        json.dump(lst, f, indent=2)
