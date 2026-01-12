from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, JSONResponse
import uvicorn

app = FastAPI(title="Ping Pong App")

# Counter stored in memory
counter = 0


@app.get("/pingpong", response_class=PlainTextResponse)
async def pingpong():
    """Respond with pong and increment counter"""
    global counter
    response = f"pong {counter}"
    counter += 1
    return response


@app.get("/pings")
async def get_pings():
    """Return the current ping-pong count"""
    return JSONResponse(content={"count": counter})


@app.get("/")
async def root():
    return {"message": "Ping Pong App - Use /pingpong endpoint"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
