import redis
import json
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def build_cache_key(query: str, page: int, page_size: int):
    return f"query:{query}:page:{page}:size:{page_size}"


def get_cached_query(query: str, page: int, page_size: int):

    key = build_cache_key(query, page, page_size)

    cached = redis_client.get(key)

    if cached:
        return json.loads(cached)

    return None


def cache_query(query: str, page: int, page_size: int, data):

    key = build_cache_key(query, page, page_size)

    redis_client.setex(
        key,
        300,  # cache for 5 minutes
        json.dumps(data)
    )

def clear_cache():
    redis_client.flushall()