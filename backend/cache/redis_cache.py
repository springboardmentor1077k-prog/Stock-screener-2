import redis
import json
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def build_cache_key(cache_key: str, page: int, page_size: int):
    return f"query:{cache_key}:page:{page}:size:{page_size}"


def get_cached_query(cache_key: str, page: int, page_size: int):
    try:
        key = build_cache_key(cache_key, page, page_size)
        cached = redis_client.get(key)

        if cached:
            return json.loads(cached)

        return None
    except Exception:
        return None


def cache_query(cache_key: str, page: int, page_size: int, data):
    try:
        key = build_cache_key(cache_key, page, page_size)

        redis_client.setex(
            key,
            300,  # 5 min cache
            json.dumps(data)
        )
    except Exception:
        pass


def clear_cache():
    try:
        redis_client.flushall()
    except Exception:
        pass