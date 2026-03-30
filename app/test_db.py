from db import get_connection

try:
    conn = get_connection()
    print("✅ DB Connected Successfully")
    conn.close()
except Exception as e:
    print("❌ Error:", e)