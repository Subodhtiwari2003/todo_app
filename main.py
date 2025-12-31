from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from contextlib import contextmanager, asynccontextmanager
import sqlite3

# Database Configuration
DATABASE = "todo.db"

# Pydantic Models
class TaskModel(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    status: str = "Pending"

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[str]
    status: str

class TaskUpdate(BaseModel):
    status: str

# Database Helper Functions
@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize database and create tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'Pending',
                due_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# Lifespan event handler (replaces deprecated on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (if needed)

# FastAPI App
app = FastAPI(lifespan=lifespan)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints
@app.post("/api/tasks", response_model=TaskResponse)
def create_task(task: TaskModel):
    """Create a new task"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, description, status, due_date) VALUES (?,?,?,?)",
            (task.title, task.description, task.status, task.due_date)
        )
        task_id = cursor.lastrowid
        
        # Fetch the created task
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "due_date": row["due_date"],
            "status": row["status"]
        }

@app.get("/api/tasks", response_model=list[TaskResponse])
def get_tasks():
    """Retrieve all tasks"""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM tasks ORDER BY id DESC")
        tasks = cursor.fetchall()
        
        return [
            {
                "id": task["id"],
                "title": task["title"],
                "description": task["description"],
                "due_date": task["due_date"],
                "status": task["status"]
            }
            for task in tasks
        ]

@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int):
    """Retrieve a specific task"""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "id": task["id"],
            "title": task["title"],
            "description": task["description"],
            "due_date": task["due_date"],
            "status": task["status"]
        }

@app.patch("/api/tasks/{task_id}", response_model=TaskResponse)
def update_task_status(task_id: int, task_update: TaskUpdate):
    """Update task status"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if task exists
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Update status
        cursor.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            (task_update.status, task_id)
        )
        
        # Fetch updated task
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        
        return {
            "id": task["id"],
            "title": task["title"],
            "description": task["description"],
            "due_date": task["due_date"],
            "status": task["status"]
        }

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    """Delete a task"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if task exists
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Delete task
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        
        return {"message": "Task deleted successfully"}

# Serve static files and HTML
@app.get("/")
def read_root():
    """Serve the main HTML page"""
    return FileResponse("index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)