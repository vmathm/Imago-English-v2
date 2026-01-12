import os
import time
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL is not set", file=sys.stderr)
    sys.exit(1)

timeout_s = int(os.environ.get("DB_WAIT_TIMEOUT", "60"))
interval_s = float(os.environ.get("DB_WAIT_INTERVAL", "1.5"))

deadline = time.time() + timeout_s
last_error = None

print(f"⏳ Waiting for database up to {timeout_s}s...")

while time.time() < deadline:
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database is ready")
        sys.exit(0)
    except Exception as e:
        last_error = e
        print(f"… DB not ready yet: {e.__class__.__name__}")
        time.sleep(interval_s)

print(f"❌ Database not ready after {timeout_s}s. Last error: {last_error}", file=sys.stderr)
sys.exit(1)