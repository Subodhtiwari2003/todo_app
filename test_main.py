import pytest
from fastapi.testclient import TestClient
from main import app, init_db
import sqlite3
import os

# Use a separate test database
TEST_DATABASE = "test_todo.db"

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test"""
    # Override the database name
    import main
    main.DATABASE = TEST_DATABASE
    
    # Initialize the database
    init_db()
    
    yield
    
    # Cleanup: remove the test database after each test
    if os.path.exists(TEST_DATABASE):
        os.remove(TEST_DATABASE)

@pytest.fixture
def client(test_db):
    """Create a test client"""
    return TestClient(app)

def test_create_task(client):
    """Test creating a new task"""
    response = client.post("/api/tasks", json={
        "title": "Test Task",
        "description": "Testing Description",
        "status": "Pending",
        "due_date": "2023-12-31"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Testing Description"
    assert data["status"] == "Pending"
    assert data["due_date"] == "2023-12-31"
    assert "id" in data

def test_read_tasks(client):
    """Test retrieving all tasks"""
    # Create a task first
    client.post("/api/tasks", json={
        "title": "Test Task 1",
        "description": "Description 1"
    })
    
    # Get all tasks
    response = client.get("/api/tasks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["title"] == "Test Task 1"

def test_get_single_task(client):
    """Test retrieving a single task"""
    # Create a task
    create_response = client.post("/api/tasks", json={
        "title": "Single Task",
        "description": "Single Description"
    })
    task_id = create_response.json()["id"]
    
    # Get the task
    response = client.get(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Single Task"

def test_update_task_status(client):
    """Test updating task status"""
    # Create a task
    create_response = client.post("/api/tasks", json={
        "title": "Task to Update"
    })
    task_id = create_response.json()["id"]
    
    # Update status
    response = client.patch(f"/api/tasks/{task_id}", json={
        "status": "Completed"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Completed"

def test_delete_task(client):
    """Test deleting a task"""
    # Create a task
    create_response = client.post("/api/tasks", json={
        "title": "Delete Me"
    })
    task_id = create_response.json()["id"]
    
    # Delete the task
    response = client.delete(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Task deleted successfully"
    
    # Verify it's deleted
    get_response = client.get(f"/api/tasks/{task_id}")
    assert get_response.status_code == 404

def test_task_not_found(client):
    """Test 404 for non-existent task"""
    response = client.get("/api/tasks/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"

def test_delete_nonexistent_task(client):
    """Test deleting non-existent task"""
    response = client.delete("/api/tasks/9999")
    assert response.status_code == 404