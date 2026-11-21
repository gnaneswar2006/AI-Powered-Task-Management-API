from fastapi.testclient import TestClient

from app.main import app, tasks

client = TestClient(app)


def setup_function():
    tasks.clear()


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

    updated = client.patch(
        f"/tasks/{task_id}", json={"title": "Read a book", "completed": True}
    )
    assert updated.status_code == 200
    assert updated.json()["priority"] == "low"
    assert updated.json()["completed"] is True

    assert client.delete(f"/tasks/{task_id}").status_code == 204
    assert client.get(f"/tasks/{task_id}").status_code == 404


def test_validation():
    assert client.post("/tasks", json={"title": ""}).status_code == 422
    assert client.get("/tasks/999999").status_code == 404
