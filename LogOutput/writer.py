import secrets
import string
import time
from datetime import datetime

# Generate random string on startup
def generate_random_string(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

def now_timestamp() -> str:
    return datetime.now().isoformat(sep=" ", timespec="seconds")

# File path in shared volume
LOG_FILE = "/shared/log.txt"

# Generate random string on startup
stored_value = generate_random_string()

# Write to file every 5 seconds
if __name__ == "__main__":
    while True:
        log_line = f"{now_timestamp()} {stored_value}\n"
        with open(LOG_FILE, "a") as f:
            f.write(log_line)
            f.flush()
        print(f"Written: {log_line.strip()}", flush=True)
        time.sleep(5)
