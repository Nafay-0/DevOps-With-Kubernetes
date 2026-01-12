import secrets
import string
import time
import os
import requests
from datetime import datetime

# Generate random string on startup
def generate_random_string(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

def now_timestamp() -> str:
    return datetime.now().isoformat(sep=" ", timespec="seconds")

# File path in shared volume (only for log output, not for pingpong count)
LOG_FILE = "/shared/log.txt"
# PingPong service URL from environment variable
PINGPONG_SERVICE_URL = os.getenv("PINGPONG_SERVICE_URL", "http://pingpong-service.exercises:80")

def get_pingpong_count():
    """Get ping-pong counter via HTTP from PingPong service"""
    try:
        response = requests.get(f"{PINGPONG_SERVICE_URL}/pings", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data.get("count", 0)
        return 0
    except Exception as e:
        print(f"Error fetching ping-pong count: {e}", flush=True)
        return 0

# ConfigMap file path
CONFIG_FILE = "/config/information.txt"

def read_config_file():
    """Read content from ConfigMap file"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return f.read().strip()
        return ""
    except Exception as e:
        print(f"Error reading config file: {e}", flush=True)
        return ""

# Generate random string on startup
stored_value = generate_random_string()

# Write to file every 5 seconds
if __name__ == "__main__":
    # Read ConfigMap values once at startup
    config_file_content = read_config_file()
    message_env = os.getenv("MESSAGE", "")
    
    # Print ConfigMap values
    print(f"file content: {config_file_content}", flush=True)
    print(f"env variable: MESSAGE={message_env}", flush=True)
    
    while True:
        pingpong_count = get_pingpong_count()
        # Format: ISO timestamp with Z: random_string.\nPing / Pongs: count
        timestamp_iso = datetime.now().isoformat(timespec='milliseconds') + 'Z'
        log_line = f"{timestamp_iso}: {stored_value}.\nPing / Pongs: {pingpong_count}\n"
        with open(LOG_FILE, "a") as f:
            f.write(log_line)
            f.flush()
        print(f"Written: {log_line.strip()}", flush=True)
        time.sleep(5)
