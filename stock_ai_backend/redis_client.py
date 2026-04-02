import redis
import json

# Connect to Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print("✅ Connected to Redis")
except Exception as e:
    print("❌ Redis connection failed:", e)
    r = None


# GET CACHE
def get_cache(key):
    if not r:
        return None

    data = r.get(key)
    if data:
        return json.loads(data)
    return None


# SET CACHE
def set_cache(key, value):
    if not r:
        return

    r.set(key, json.dumps(value), ex=300)  # expires in 5 min
