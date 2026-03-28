import redis


# Redis connection
cache = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

cache.set("test_key", "hello")
print(cache.get("test_key"))