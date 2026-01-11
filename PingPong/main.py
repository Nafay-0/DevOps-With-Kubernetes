from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import uvicorn
import os

app = FastAPI(title="Ping Pong App")

# File path in persistent volume
COUNTER_FILE = "/shared/pingpong-count.txt"


def read_counter():
    """Read counter from file"""
    try:
        if os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, "r") as f:
                content = f.read().strip()
                return int(content) if content else 0
        return 0
    except Exception:
        return 0


def write_counter(count):
    """Write counter to file"""
    try:
        os.makedirs(os.path.dirname(COUNTER_FILE), exist_ok=True)
        with open(COUNTER_FILE, "w") as f:
            f.write(str(count))
            f.flush()
    except Exception as e:
        print(f"Error writing counter: {e}", flush=True)


@app.get("/pingpong", response_class=PlainTextResponse)
async def pingpong():
    """Respond with pong and increment counter"""
    counter = read_counter()
    response = f"pong {counter}"
    counter += 1
    write_counter(counter)
    return response


@app.get("/")
async def root():
    return {"message": "Ping Pong App - Use /pingpong endpoint"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
