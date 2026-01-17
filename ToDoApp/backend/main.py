from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError
import uvicorn
import os
import psycopg2
import time
import logging
from contextlib import contextmanager
from typing import List
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Todo Backend API")

# Enable CORS to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors and log them"""
    client_ip = request.client.host if request.client else "unknown"
    errors = exc.errors()
    
    # Extract the content length and value from validation errors
    content_length = None
    content_value = None
    for error in errors:
        if "content" in str(error.get("loc", [])):
            if "string_too_long" in str(error.get("type", "")) or "max_length" in str(error.get("type", "")):
                # Get the actual content from the error input
                content_value = error.get("input", "")
                if content_value:
                    content_length = len(content_value)
                    error_msg = f"Todo content cannot exceed 140 characters (received {content_length} characters)"
                    logger.warning(f"POST /todos - REJECTED (Validation Error): {error_msg} from {client_ip}")
                    logger.warning(f"POST /todos - Rejected content: {content_value[:100]}{'...' if len(content_value) > 100 else ''}")
                    break
    
    if not content_length:
        # Log generic validation error
        logger.warning(f"POST /todos - REJECTED (Validation Error) from {client_ip}: {errors}")
    
    # Return the default validation error response
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=422,
        content={"detail": errors}
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
    content: str = Field(..., max_length=140, min_length=1, description="Todo content (max 140 characters)")


@app.get("/todos")
async def get_todos():
    """Get all todos from database"""
    logger.info("GET /todos - Request received to fetch all todos")
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT content FROM todos ORDER BY created_at DESC;")
            todos = [row[0] for row in cur.fetchall()]
            cur.close()
            logger.info(f"GET /todos - Successfully retrieved {len(todos)} todos")
            return {"todos": todos}
    except Exception as e:
        logger.error(f"GET /todos - Error retrieving todos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving todos: {str(e)}")


@app.post("/todos")
async def create_todo(todo: TodoCreate, request: Request):
    """Create a new todo in database"""
    content_length = len(todo.content)
    client_ip = request.client.host if request.client else "unknown"
    
    logger.info(f"POST /todos - Request received from {client_ip} - Content length: {content_length} characters")
    logger.info(f"POST /todos - Todo content: {todo.content[:100]}{'...' if len(todo.content) > 100 else ''}")
    
    # Validate content length (140 character limit)
    if content_length > 140:
        error_msg = f"Todo content cannot exceed 140 characters (received {content_length} characters)"
        logger.warning(f"POST /todos - REJECTED: {error_msg} - Content: {todo.content[:100]}...")
        raise HTTPException(status_code=400, detail=error_msg)
    
    if not todo.content.strip():
        error_msg = "Todo content cannot be empty"
        logger.warning(f"POST /todos - REJECTED: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO todos (content) VALUES (%s) RETURNING id;", (todo.content.strip(),))
            todo_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            logger.info(f"POST /todos - SUCCESS: Todo created with ID {todo_id} - Content: {todo.content.strip()}")
            return {"message": "Todo created successfully", "todo": todo.content.strip(), "id": todo_id}
    except Exception as e:
        logger.error(f"POST /todos - ERROR creating todo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating todo: {str(e)}")


@app.get("/")
async def root():
    return {"message": "Todo Backend API", "endpoints": ["GET /todos", "POST /todos"]}

@app.get("/healthz")
async def healthz():
    """Readiness/Liveness check: only OK when DB is reachable."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=2
        )
        conn.close()
        return {"status": "ok"}
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"status": "db unavailable", "error": str(e)})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
