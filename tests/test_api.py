import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("TASK_DB_PATH", str(tmp_path / "test.db"))


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_task_lifecycle():
    response = client.post("/tasks", json={"title": "Urgent deadline"})
    assert response.status_code == 201
    task = response.json()
    assert task["priority"] == "high"
    task_id = task["id"]
    assert client.get(f"/tasks/{task_id}").status_code == 200
    assert len(client.get("/tasks").json()) == 1
    updated = client.patch(f"/tasks/{task_id}", json={"title": "Read a book", "completed": True})
    assert updated.status_code == 200
    assert updated.json()["priority"] == "low"
    assert updated.json()["completed"] is True
    assert client.delete(f"/tasks/{task_id}").status_code == 204
    assert client.get(f"/tasks/{task_id}").status_code == 404


def test_validation():
    assert client.post("/tasks", json={"title": ""}).status_code == 422
    assert client.get("/tasks/999999").status_code == 404


def test_persists_across_connections():
    task = client.post("/tasks", json={"title": "Write tests"}).json()
    assert client.get(f"/tasks/{task['id']}").json()["title"] == "Write tests"


def test_reject_null_updates():
    task = client.post("/tasks", json={"title": "Keep title"}).json()
    assert client.patch(f"/tasks/{task['id']}", json={"title": None}).status_code == 422
