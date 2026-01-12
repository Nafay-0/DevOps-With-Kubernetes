from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import os
import psycopg2
import time
from contextlib import contextmanager
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

# Database connection parameters from environment variables
DB_HOST = os.getenv("DB_HOST", "postgres-stset-0.postgres-service.project")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "tododb")
DB_USER = os.getenv("DB_USER", "todouser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    max_retries = 10
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            yield conn
            conn.close()
            return
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                print(f"Database connection failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying...", flush=True)
                time.sleep(retry_delay)
            else:
                print(f"Database connection failed after {max_retries} attempts: {e}", flush=True)
                raise


def init_database():
    """Initialize database table if it doesn't exist"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id SERIAL PRIMARY KEY,
                    content VARCHAR(140) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cur.close()
            print("Database initialized successfully", flush=True)
    except Exception as e:
        print(f"Error initializing database: {e}", flush=True)


@app.on_event("startup")
async def startup_event():
    """Initialize database when app starts"""
    print("Initializing database connection...", flush=True)
    init_database()


class TodoCreate(BaseModel):
    content: str = Field(..., max_length=140, description="Todo content (max 140 characters)")


@app.get("/todos")
async def get_todos():
    """Get all todos from database"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT content FROM todos ORDER BY created_at DESC;")
            todos = [row[0] for row in cur.fetchall()]
            cur.close()
            return {"todos": todos}
    except Exception as e:
        print(f"Error getting todos: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving todos: {str(e)}")


@app.post("/todos")
async def create_todo(todo: TodoCreate):
    """Create a new todo in database"""
    if len(todo.content) > 140:
        raise HTTPException(status_code=400, detail="Todo content cannot exceed 140 characters")
    
    if not todo.content.strip():
        raise HTTPException(status_code=400, detail="Todo content cannot be empty")
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO todos (content) VALUES (%s) RETURNING id;", (todo.content.strip(),))
            todo_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            return {"message": "Todo created successfully", "todo": todo.content.strip(), "id": todo_id}
    except Exception as e:
        print(f"Error creating todo: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"Error creating todo: {str(e)}")


@app.get("/")
async def root():
    return {"message": "Todo Backend API", "endpoints": ["GET /todos", "POST /todos"]}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
