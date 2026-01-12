import os
import signal
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
import requests

load_dotenv()

app = FastAPI(title="ToDo App v1.0")

# Cache directory in volume
CACHE_DIR = "/cache"
IMAGE_FILE = os.path.join(CACHE_DIR, "image.jpg")
TIMESTAMP_FILE = os.path.join(CACHE_DIR, "timestamp.txt")

# Ensure cache directory exists
try:
    os.makedirs(CACHE_DIR, exist_ok=True)
    print(f"Cache directory created/verified: {CACHE_DIR}", flush=True)
except Exception as e:
    print(f"Error creating cache dir: {e}", flush=True)


def fetch_and_save_image():
    """Fetch a new image from Lorem Picsum and save it"""
    try:
        print("Fetching image from Lorem Picsum...", flush=True)
        url = "https://picsum.photos/1200"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        print(f"Image fetched, size: {len(response.content)} bytes", flush=True)
        
        # Save image
        with open(IMAGE_FILE, "wb") as f:
            f.write(response.content)
        print(f"Image saved to {IMAGE_FILE}", flush=True)
        
        # Save timestamp
        with open(TIMESTAMP_FILE, "w") as f:
            f.write(datetime.now().isoformat())
        print("Timestamp saved", flush=True)
        
        return True
    except Exception as e:
        print(f"Error fetching/saving image: {e}", flush=True)
        return False


def should_refresh_image():
    """Check if image should be refreshed (older than 10 minutes)"""
    try:
        if not os.path.exists(IMAGE_FILE) or not os.path.exists(TIMESTAMP_FILE):
            return True
        
        with open(TIMESTAMP_FILE, "r") as f:
            timestamp_str = f.read().strip()
            cached_time = datetime.fromisoformat(timestamp_str)
        
        elapsed = datetime.now() - cached_time
        return elapsed >= timedelta(minutes=10)
    except Exception as e:
        print(f"Error checking refresh: {e}", flush=True)
        return True


@app.get("/image")
async def get_image():
    """Serve the cached image"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        
        # Check if we need to fetch/refresh
        should_refresh = await loop.run_in_executor(None, should_refresh_image)
        if should_refresh:
            print("Need to refresh image", flush=True)
            await loop.run_in_executor(None, fetch_and_save_image)
        
        exists = await loop.run_in_executor(None, os.path.exists, IMAGE_FILE)
        if exists:
            return FileResponse(IMAGE_FILE, media_type="image/jpeg")
        else:
            return JSONResponse(content={"error": "Image not available"}, status_code=404)
    except Exception as e:
        print(f"Error in get_image: {e}", flush=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Todo App</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
            }
            h1 {
                color: #333;
            }
            .todo-item {
                padding: 10px;
                margin: 5px 0;
                background-color: #f5f5f5;
                border-left: 3px solid #4CAF50;
            }
            .image-container {
                margin: 20px 0;
                text-align: center;
            }
            .image-container img {
                max-width: 100%;
                height: auto;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
        </style>
    </head>
    <body>
        <h1>My Todo List</h1>
        <div class="image-container">
            <img src="/image" alt="Random image from Lorem Picsum" />
        </div>
        <div class="todo-item">Sample todo item 1</div>
        <div class="todo-item">Sample todo item 2</div>
        <div class="todo-item">Sample todo item 3</div>
    </body>
    </html>
    """
    return html_content


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    print("\nShutting down gracefully...", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    port = int(os.getenv("PORT", 8000))
    print(f"Server started in port {port}", flush=True)
    
    uvicorn.run(app, host="0.0.0.0", port=port)
