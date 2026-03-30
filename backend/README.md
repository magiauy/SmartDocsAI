# SmartDocsAI Backend

## Setup

1. Create a Python environment.
2. Install dependencies from `requirements/dev.txt`.
3. Copy `.env.example` to `.env`.
4. Run migrations.
5. Start Django and Celery worker.
6. Run tests with `pytest`.

## Runtime Modes

- Local Python + external MySQL
- Docker Compose with external MySQL
- Docker Compose with the optional MySQL profile enabled

## Common Commands

```powershell
Copy-Item .env.example .env
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py runserver
.venv\Scripts\celery.exe -A app worker -l info
.venv\Scripts\pytest.exe -v
docker compose up web worker redis qdrant
docker compose --profile mysql up
```
