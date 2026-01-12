from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from typing import List

app = FastAPI(title="Todo Backend API")

# Enable CORS to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for todos
todos: List[str] = []


class TodoCreate(BaseModel):
    content: str = Field(..., max_length=140, description="Todo content (max 140 characters)")


@app.get("/todos")
async def get_todos():
    """Get all todos"""
    return {"todos": todos}


@app.post("/todos")
async def create_todo(todo: TodoCreate):
    """Create a new todo"""
    if len(todo.content) > 140:
        raise HTTPException(status_code=400, detail="Todo content cannot exceed 140 characters")
    
    if not todo.content.strip():
        raise HTTPException(status_code=400, detail="Todo content cannot be empty")
    
    todos.append(todo.content.strip())
    return {"message": "Todo created successfully", "todo": todo.content.strip()}


@app.get("/")
async def root():
    return {"message": "Todo Backend API", "endpoints": ["GET /todos", "POST /todos"]}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
