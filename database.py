import sqlite3
from contextlib import contextmanager

DB_NAME = "todo.db"

# Context manager to handle database connections automatically
@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    # This allows accessing columns by name (row["title"]) instead of index
    conn.row_factory = sqlite3.Row 
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the database with the tasks table."""
    schema = """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'Pending',
        due_date TEXT
    );
    """
    with get_db_connection() as conn:
        conn.execute(schema)
        conn.commit()
        print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()