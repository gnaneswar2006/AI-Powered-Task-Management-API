"""Task management API backed by SQLite."""
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import database

app = FastAPI(title="AI-Powered Task Management API", version="0.2.0")


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    completed: bool = False


class Task(TaskCreate):
    id: int
    priority: Priority
    created_at: datetime


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool | None = None


def recommend_priority(title: str, description: str) -> Priority:
    """Explainable keyword baseline, not a trained AI model."""
    text = f"{title} {description}".lower()
    if any(word in text for word in ("urgent", "deadline", "critical", "asap")):
        return Priority.high
    if any(word in text for word in ("important", "review", "meeting")):
        return Priority.medium
    return Priority.low


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(payload: TaskCreate):
    data = payload.model_dump()
    data["priority"] = recommend_priority(payload.title, payload.description).value
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    return database.insert_task(data)


@app.get("/tasks", response_model=list[Task])
def list_tasks():
    return database.list_tasks()


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    task = database.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate):
    changes = payload.model_dump(exclude_unset=True)
    if any(value is None for value in changes.values()):
        raise HTTPException(status_code=422, detail="Task fields cannot be null")
    current = database.get_task(task_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Task not found")
    title = changes.get("title", current["title"])
    description = changes.get("description", current["description"])
    changes["priority"] = recommend_priority(title, description).value
    return database.update_task(task_id, changes)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    if not database.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
