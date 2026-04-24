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

## RAG Runtime Notes

- OCR endpoint is configured via `PADDLEOCR_API_URL` and can point to an external PaddleOCR provider.
- External OCR auth/request options:
	- `PADDLEOCR_API_KEY`
	- `PADDLEOCR_API_KEY_HEADER` (default: `Authorization`)
	- `PADDLEOCR_API_KEY_PREFIX` (default: `Bearer`)
	- `PADDLEOCR_REQUEST_MODE` (`aistudio-job`, `multipart`, or `base64-json`)
	- `PADDLEOCR_FILE_FIELD` (default: `file`)
	- `PADDLEOCR_EXTRA_PARAMS_JSON` (JSON object string for vendor-specific options)
- AIStudio async job mode options:
	- `PADDLEOCR_MODEL` (for example: `PaddleOCR-VL-1.5`)
	- `PADDLEOCR_OPTIONAL_PAYLOAD_JSON` (JSON object for `optionalPayload`)
	- `PADDLEOCR_JOB_POLL_SECONDS` and `PADDLEOCR_JOB_TIMEOUT_SECONDS`
- Embedding uses Gemini API by default (`EMBEDDING_PROVIDER=gemini`, model `gemini-embedding-2-preview`).
- Embedding config options:
	- `EMBEDDING_PROVIDER`
	- `EMBEDDING_MODEL_NAME`
	- `EMBEDDING_VECTOR_SIZE`
	- `EMBEDDING_TIMEOUT_SECONDS`
	- `EMBEDDING_GEMINI_TASK_TYPE_DOCUMENT`
	- `EMBEDDING_GEMINI_TASK_TYPE_QUERY`
- Retrieval backend can be selected with `RETRIEVAL_STORE_BACKEND`:
	- `qdrant` (default)
	- `neo4j` (Graph RAG base with chunk nodes + `NEXT` relationships + vector index)
- Neo4j retrieval config options:
	- `NEO4J_URI`
	- `NEO4J_USER`
	- `NEO4J_PASSWORD`
	- `NEO4J_DATABASE`
	- `NEO4J_VECTOR_INDEX_NAME`
	- `NEO4J_VECTOR_SIMILARITY` (`cosine` or `euclidean`)
- Retrieval tuning is configurable with `CHUNK_SIZE`, `CHUNK_OVERLAP`, and `RETRIEVAL_TOP_K`.
- Chat session window is configurable with `SESSION_MEMORY_MAX_TURNS`.

## Frontend Local End-to-End

Run backend services with Docker and run Streamlit frontend from workspace root.

1. Start backend stack:
	- `cd backend`
	- `docker compose up web worker redis qdrant`
2. Run frontend in another terminal at workspace root:
	- `pip install -r requirement.txt`
	- `$env:SMARTDOCSAI_API_BASE_URL='http://localhost:8000'`
	- `streamlit run frontend/index.py`

Optional frontend runtime tuning vars:
- `SMARTDOCSAI_FE_POLL_INTERVAL_SECONDS` (default: `2`)
- `SMARTDOCSAI_FE_DOCUMENT_TIMEOUT_SECONDS` (default: `180`)
- `SMARTDOCSAI_FE_CONVERSATION_TIMEOUT_SECONDS` (default: `120`)

## Common Commands

```powershell
Copy-Item .env.example .env
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py runserver
.venv\Scripts\celery.exe -A app worker -l info
.venv\Scripts\pytest.exe -v
docker compose up web worker redis qdrant
docker compose --profile ollama up web worker redis qdrant ollama
docker compose --profile mysql up
pip install -r ..\requirement.txt
$env:SMARTDOCSAI_API_BASE_URL='http://localhost:8000'; streamlit run ..\frontend\index.py

# Run tests with SQLite override (when MySQL container is not running)
$env:DB_ENGINE=''; .venv\Scripts\pytest.exe -v
```

## Demo Page

Start the Django server, then open `/demo/` to access the browser demo for:

- multi-file document upload
- conversation creation
- bootstrap summary polling
- chat requests against the current backend APIs
