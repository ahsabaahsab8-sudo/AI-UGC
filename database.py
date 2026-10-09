import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import DATABASE_PATH

def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the SQLite database schema."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                no TEXT,
                product TEXT NOT NULL,
                product_photo TEXT NOT NULL,
                icp TEXT NOT NULL,
                product_features TEXT NOT NULL,
                video_setting TEXT NOT NULL,
                model TEXT NOT NULL DEFAULT 'Veo 3.1',
                status TEXT NOT NULL DEFAULT 'Ready',
                prompt_image TEXT,
                generated_image_path TEXT,
                image_analysis TEXT,
                prompt_video TEXT,
                finished_video_path TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);")
        conn.commit()

def add_task(
    product: str,
    product_photo: str,
    icp: str,
    product_features: str,
    video_setting: str,
    model: str = "Veo 3.1",
    no: Optional[str] = None,
    status: str = "Ready"
) -> int:
    """Add a new generation task to the SQLite queue."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (
                no, product, product_photo, icp, product_features, video_setting, model, status, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            no or f"TASK-{int(datetime.now().timestamp())}",
            product,
            product_photo,
            icp,
            product_features,
            video_setting,
            model,
            status,
            datetime.now().isoformat()
        ))
        conn.commit()
        return cursor.lastrowid

def get_next_ready_task() -> Optional[Dict[str, Any]]:
    """Fetch the next task with status 'Ready'."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM tasks
            WHERE status = 'Ready'
            ORDER BY id ASC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def update_task_fields(task_id: int, **kwargs):
    """Update arbitrary fields of a task."""
    if not kwargs:
        return
    kwargs["updated_at"] = datetime.now().isoformat()
    keys = list(kwargs.keys())
    set_clause = ", ".join([f"{k} = ?" for k in keys])
    values = [kwargs[k] for k in keys] + [task_id]

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        conn.commit()

def get_all_tasks(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve recent tasks."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

def get_task_by_id(task_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single task by ID."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
