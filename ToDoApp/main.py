import os
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI


load_dotenv()

app = FastAPI(title="ToDo App v1.0")


@app.get("/")
async def root():
    return {"message": "Hello from TODO App"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    print(f"Server started in port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
