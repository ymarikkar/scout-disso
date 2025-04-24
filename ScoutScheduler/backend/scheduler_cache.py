# ScoutScheduler/backend/scheduler_cache.py
from cachetools import TTLCache

# keep up to 100 prompt → suggestion sets, each valid 10 min
_cache = TTLCache(maxsize=100, ttl=600)

def get(key: str):
    return _cache.get(key)

def set(key: str, value):
    _cache[key] = value
