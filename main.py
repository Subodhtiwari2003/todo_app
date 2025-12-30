from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from database import get_db_connection, init_db

# Initialize App and DB
app = FastAPI(title="To-Do List API", description="Raw SQL CRUD API")
templates = Jinja2Templates(directory="templates")

# Run DB initialization on startup
@app.on_event("startup")
def startup():
    init_db()

# --- Pydantic Models for Data Validation ---
class TaskModel(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = "Pending"

class TaskResponse(TaskModel):
    id: int

# --- API ENDPOINTS (CRUD) ---

@app.post("/api/tasks", response_model=TaskResponse)
def create_task(task: TaskModel):
    """Create a new task using Raw SQL"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, description, status, due_date) VALUES (?,?,?,?)",
            (task.title, task.description, task.status, task.due_date)
        )
        conn.commit()
        new_id = cursor.lastrowid
        return {**task.dict(), "id": new_id}

@app.get("/api/tasks", response_model=list)
def get_tasks():
    """Retrieve all tasks"""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM tasks")
        tasks = cursor.fetchall()
        # Convert sqlite3.Row objects to dicts
        return [dict(row) for row in tasks]

@app.put("/api/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskModel):
    """Update a task"""
    with get_db_connection() as conn:
        # Check if exists first
        check = conn.execute("SELECT id FROM tasks WHERE id =?", (task_id,)).fetchone()
        if not check:
            raise HTTPException(status_code=404, detail="Task not found")
            
        conn.execute(
            "UPDATE tasks SET title=?, description=?, status=?, due_date=? WHERE id=?",
            (task.title, task.description, task.status, task.due_date, task_id)
        )
        conn.commit()
        return {**task.dict(), "id": task_id}

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    """Delete a task"""
    with get_db_connection() as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id =?", (task_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task deleted successfully"}

# --- WEB INTERFACE ROUTES ---

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """Render the HTML template with the list of tasks"""
    # Fetch tasks directly to render the initial page server-side
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM tasks")
        tasks = [dict(row) for row in cursor.fetchall()]
    return templates.TemplateResponse("index.html", {"request": request, "tasks": tasks})