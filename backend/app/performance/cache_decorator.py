import functools
import hashlib
import json

_cache = {}

def cache_result(ttl: int = 300):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = hashlib.md5(json.dumps({"args": str(args), "kwargs": str(kwargs)}).encode()).hexdigest()
            if key in _cache:
                return _cache[key]
            result = func(*args, **kwargs)
            _cache[key] = result
            return result
        return wrapper
    return decorator

def clear_cache():
    _cache.clear()
