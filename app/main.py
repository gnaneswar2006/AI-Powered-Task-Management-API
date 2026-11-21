from datetime import datetime, timezone
from enum import Enum
from itertools import count
from threading import Lock

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="AI-Powered Task Management API", version="0.1.0")


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


tasks: dict[int, Task] = {}
ids = count(1)
lock = Lock()


def recommend_priority(title: str, description: str) -> Priority:
    """Simple explainable keyword baseline; not a trained AI model."""
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
    with lock:
        task_id = next(ids)
        task = Task(
            **payload.model_dump(),
            id=task_id,
            priority=recommend_priority(payload.title, payload.description),
            created_at=datetime.now(timezone.utc),
        )
        tasks[task_id] = task
        return task


@app.get("/tasks", response_model=list[Task])
def list_tasks():
    with lock:
        return list(tasks.values())


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    with lock:
        task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate):
    with lock:
        task = tasks.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        changes = payload.model_dump(exclude_unset=True)
        if "title" in changes and changes["title"] is None:
            raise HTTPException(status_code=422, detail="Title cannot be null")
        if "description" in changes and changes["description"] is None:
            raise HTTPException(status_code=422, detail="Description cannot be null")
        if "completed" in changes and changes["completed"] is None:
            raise HTTPException(status_code=422, detail="Completed cannot be null")
        updated = task.model_copy(update=changes)
        updated.priority = recommend_priority(updated.title, updated.description)
        tasks[task_id] = updated
        return updated


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with lock:
        if tasks.pop(task_id, None) is None:
            raise HTTPException(status_code=404, detail="Task not found")
