import redis
import json

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

def normalize_key(query: str):
    return query.lower().strip()

def get_cached_query(query):

    key = normalize_key(query)

    cached = redis_client.get(key)

    if cached:
        return json.loads(cached)

    return None


def cache_query(query, data):

    key = normalize_key(query)

    redis_client.setex(
        key,
        300,
        json.dumps(data)
    )