import secrets
import string
import time
from datetime import datetime


def generate_random_string(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def now_timestamp() -> str:
    return datetime.now().isoformat(sep=" ", timespec="seconds")

    

if __name__ == "__main__":
    stored_value = generate_random_string()
    while True:
        print(f"{now_timestamp()} {stored_value}", flush=True)
        time.sleep(5)

