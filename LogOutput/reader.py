from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, JSONResponse
import uvicorn
import os
import requests

app = FastAPI(title="Log Output Reader")

# File path in shared volume
LOG_FILE = "/shared/log.txt"

# PingPong service URL for readiness checks
PINGPONG_URL = os.getenv("PINGPONG_URL") or os.getenv("PINGPONG_SERVICE_URL", "http://pingpong-service.exercises:80/pings")

@app.get("/")
async def root():
    return {"message": "Log Output App - Use /status endpoint"}


@app.get("/status", response_class=PlainTextResponse)
async def status():
    """Read and return the log file content"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                content = f.read()
            return content
        else:
            return "Log file not found yet. Waiting for writer to create it...\n"
    except Exception as e:
        return f"Error reading log file: {str(e)}\n"


@app.get("/status/json")
async def status_json():
    """Return status as JSON with latest line"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
            if lines:
                latest_line = lines[-1].strip()
                # Parse the line: "YYYY-MM-DD HH:MM:SS random_string"
                # Split by space, but timestamp has 2 parts (date and time)
                parts = latest_line.split(" ", 2)
                if len(parts) >= 3:
                    timestamp = f"{parts[0]} {parts[1]}"
                    random_string = parts[2]
                    return JSONResponse(content={
                        "timestamp": timestamp,
                        "random_string": random_string,
                        "total_lines": len(lines)
                    })
            return JSONResponse(content={
                "timestamp": None,
                "random_string": None,
                "total_lines": 0
            })
        else:
            return JSONResponse(content={
                "error": "Log file not found yet"
            })
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

@app.get("/healthz")
async def healthz():
    """Readiness probe: only ready when PingPong is reachable."""
    try:
        response = requests.get(PINGPONG_URL, timeout=2)
        if response.status_code == 200:
            return {"status": "ok"}
        return JSONResponse(status_code=500, content={"status": "pingpong unhealthy", "code": response.status_code})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "pingpong unreachable", "error": str(e)})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
