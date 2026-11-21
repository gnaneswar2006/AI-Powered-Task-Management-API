"""SQLite persistence layer for task records."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "tasks.db"


@contextmanager
def connection():
    path = os.environ.get("TASK_DB_PATH", str(DEFAULT_DB))
    with sqlite3.connect(path, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                completed INTEGER NOT NULL DEFAULT 0,
                priority TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        yield conn


def row_to_dict(row):
    if row is None:
        return None
    result = dict(row)
    result["completed"] = bool(result["completed"])
    return result


def insert_task(data):
    with connection() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, description, completed, priority, created_at) VALUES (?, ?, ?, ?, ?)",
            (data["title"], data["description"], int(data["completed"]), data["priority"], data["created_at"]),
        )
        return row_to_dict(conn.execute("SELECT * FROM tasks WHERE id=?", (cur.lastrowid,)).fetchone())


def list_tasks():
    with connection() as conn:
        return [row_to_dict(row) for row in conn.execute("SELECT * FROM tasks ORDER BY id")]


def get_task(task_id):
    with connection() as conn:
        return row_to_dict(conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())


def update_task(task_id, data):
    with connection() as conn:
        current = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if current is None:
            return None
        values = row_to_dict(current)
        values.update(data)
        conn.execute(
            "UPDATE tasks SET title=?, description=?, completed=?, priority=? WHERE id=?",
            (values["title"], values["description"], int(values["completed"]), values["priority"], task_id),
        )
        return row_to_dict(conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())


def delete_task(task_id):
    with connection() as conn:
        return conn.execute("DELETE FROM tasks WHERE id=?", (task_id,)).rowcount > 0
