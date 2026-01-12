from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, JSONResponse
import uvicorn
import os
import psycopg2
import time
from contextlib import contextmanager

app = FastAPI(title="Ping Pong App")

# Database connection parameters from environment variables
DB_HOST = os.getenv("DB_HOST", "postgres-service.exercises")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "pingpongdb")
DB_USER = os.getenv("DB_USER", "pingponguser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "pingpongpass")


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
                CREATE TABLE IF NOT EXISTS pingpong_counter (
                    id SERIAL PRIMARY KEY,
                    counter INTEGER NOT NULL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # Insert initial counter if table is empty
            cur.execute("SELECT COUNT(*) FROM pingpong_counter;")
            if cur.fetchone()[0] == 0:
                cur.execute("INSERT INTO pingpong_counter (counter) VALUES (0);")
            conn.commit()
            cur.close()
            print("Database initialized successfully", flush=True)
    except Exception as e:
        print(f"Error initializing database: {e}", flush=True)


def get_counter():
    """Get current counter from database"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT counter FROM pingpong_counter ORDER BY id DESC LIMIT 1;")
            result = cur.fetchone()
            cur.close()
            return result[0] if result else 0
    except Exception as e:
        print(f"Error getting counter: {e}", flush=True)
        return 0


def increment_counter():
    """Increment counter in database and return new value"""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            # Get current counter
            cur.execute("SELECT counter FROM pingpong_counter ORDER BY id DESC LIMIT 1 FOR UPDATE;")
            result = cur.fetchone()
            current_count = result[0] if result else 0
            
            # Increment and update
            new_count = current_count + 1
            cur.execute("UPDATE pingpong_counter SET counter = %s, updated_at = CURRENT_TIMESTAMP WHERE id = (SELECT id FROM pingpong_counter ORDER BY id DESC LIMIT 1);", (new_count,))
            conn.commit()
            cur.close()
            return new_count
    except Exception as e:
        print(f"Error incrementing counter: {e}", flush=True)
        return 0


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database when app starts"""
    print("Initializing database connection...", flush=True)
    init_database()


@app.get("/pingpong", response_class=PlainTextResponse)
async def pingpong():
    """Respond with pong and increment counter"""
    counter = increment_counter()
    return f"pong {counter}"


@app.get("/pings")
async def get_pings():
    """Return the current ping-pong count"""
    counter = get_counter()
    return JSONResponse(content={"count": counter})


@app.get("/")
async def root():
    return {"message": "Ping Pong App - Use /pingpong endpoint"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
