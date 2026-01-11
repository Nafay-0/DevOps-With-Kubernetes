import secrets
import string
import time
import threading
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Log Output App")

# Generate random string on startup and store in memory
def generate_random_string(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

stored_value = generate_random_string()


def now_timestamp() -> str:
    return datetime.now().isoformat(sep=" ", timespec="seconds")


def log_loop():
    """Background thread that logs every 5 seconds"""
    while True:
        print(f"{now_timestamp()} {stored_value}", flush=True)
        time.sleep(5)


@app.get("/")
async def root():
    return {"message": "Log Output App - Use /status endpoint"}


@app.get("/status")
async def status():
    """Return current status: timestamp and random string"""
    return JSONResponse(content={
        "timestamp": now_timestamp(),
        "random_string": stored_value
    })


if __name__ == "__main__":
    # Start background logging thread
    log_thread = threading.Thread(target=log_loop, daemon=True)
    log_thread.start()
    
    # Start FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000)

