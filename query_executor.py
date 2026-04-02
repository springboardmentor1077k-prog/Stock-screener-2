import psycopg2
import redis
import json
import hashlib
from decimal import Decimal  # ✅ ADD THIS

# ✅ Initialize Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def generate_cache_key(sql, params):
    """
    Create a unique cache key using SQL + params
    """
    raw_key = sql + str(params)
    return "screener:" + hashlib.md5(raw_key.encode()).hexdigest()


# ✅ NEW HELPER FUNCTION
def convert_value(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def execute_query(sql, params):
    try:
        # 🔥 1. Generate cache key
        cache_key = generate_cache_key(sql, params)

        # 🔥 2. Check Redis cache
        cached_data = redis_client.get(cache_key)
        if cached_data:
            print("⚡ CACHE HIT")
            return json.loads(cached_data)

        print("❌ CACHE MISS")

        # ✅ Connect to PostgreSQL
        conn = psycopg2.connect(
            host="localhost",
            database="stocks_db",
            user="postgres",
            password="Taekookilu"
        )

        cursor = conn.cursor()

        # ✅ Execute query
        cursor.execute(sql, params)

        # ✅ Get column names
        columns = [desc[0] for desc in cursor.description]

        # ✅ Fetch data
        rows = cursor.fetchall()

        # ✅ Convert rows → list of dicts (FIX APPLIED HERE)
        results = []
        for row in rows:
            row_dict = {}
            for i in range(len(columns)):
                value = row[i]

                # 🔥 FIX: Convert Decimal → float
                value = convert_value(value)

                row_dict[columns[i]] = value

            results.append(row_dict)

        # ✅ Close connection
        cursor.close()
        conn.close()

        # 🔥 3. Store result in Redis (FIX HERE)
        redis_client.setex(cache_key, 300, json.dumps(results, default=float))

        return results

    except Exception as e:
        print("DB ERROR:", str(e))
        raise e