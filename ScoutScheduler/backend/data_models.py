# ScoutScheduler/backend/data_models.py

from typing import List, Optional
from pydantic import BaseModel

class Badge(BaseModel):
    title: str
    url: str
    completed: bool = False

class Session(BaseModel):
    date: str
    time: str
    title: str

class Preferences(BaseModel):
    # example field — add whatever you need here
    default_schedule: List[Session] = []
