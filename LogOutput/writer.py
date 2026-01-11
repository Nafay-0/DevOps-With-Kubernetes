import secrets
import string
import time
import os
from datetime import datetime

# Generate random string on startup
def generate_random_string(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

def now_timestamp() -> str:
    return datetime.now().isoformat(sep=" ", timespec="seconds")

# File paths in shared volume
LOG_FILE = "/shared/log.txt"
PINGPONG_COUNTER_FILE = "/shared/pingpong-count.txt"

def read_pingpong_count():
    """Read ping-pong counter from file"""
    try:
        if os.path.exists(PINGPONG_COUNTER_FILE):
            with open(PINGPONG_COUNTER_FILE, "r") as f:
                content = f.read().strip()
                return int(content) if content else 0
        return 0
    except Exception:
        return 0

# Generate random string on startup
stored_value = generate_random_string()

# Write to file every 5 seconds
if __name__ == "__main__":
    while True:
        pingpong_count = read_pingpong_count()
        # Format: ISO timestamp with Z: random_string.\nPing / Pongs: count
        timestamp_iso = datetime.now().isoformat(timespec='milliseconds') + 'Z'
        log_line = f"{timestamp_iso}: {stored_value}.\nPing / Pongs: {pingpong_count}\n"
        with open(LOG_FILE, "a") as f:
            f.write(log_line)
            f.flush()
        print(f"Written: {log_line.strip()}", flush=True)
        time.sleep(5)
