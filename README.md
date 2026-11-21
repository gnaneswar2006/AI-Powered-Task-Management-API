# AI-Powered Task Management API

Python FastAPI task manager with explainable keyword-based priority recommendations.

## Features
- Create, list, retrieve, update and delete tasks
- Automatic keyword-based priorities (low, medium, high)
- Input validation and API tests
- Interactive Swagger docs at `/docs`

**Current limitations:** The priority recommendation is rule-based, not a trained AI model. Tasks are stored in memory and disappear when the server restarts. SQLite persistence, authentication and ML are planned.

## Setup
Requires Python 3.10+.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs.

## Run tests
```bash
pytest -q
```

## Example
POST `/tasks`:

```json
{"title": "Urgent project deadline", "description": "Finish API"}
```

The response includes a high priority recommendation.

## Next milestones
1. Persist tasks with SQLite and SQLAlchemy
2. Add secure user authentication
3. Add due dates, filtering, and pagination
4. Evaluate a trained ML priority model
5. Set up continuous integration and deployment
