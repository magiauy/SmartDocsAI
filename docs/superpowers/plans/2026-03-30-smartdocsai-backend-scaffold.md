# SmartDocsAI Backend Scaffold Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold a Django + DRF backend for SmartDocsAI with MySQL, Celery/Redis background jobs, Qdrant retrieval boundaries, Gemini/Ollama LLM adapters, mock fallback behavior, persisted chat history, and baseline APIs for documents, conversations, messages, providers, and health.

**Architecture:** Build a modular monolith under `backend/` with domain apps for `core`, `documents`, `chat`, `llm`, `retrieval`, `jobs`, and `mock_data`. Keep request handling thin and move normalization, chunking, indexing, and summarization into Celery tasks; route retrieval and provider calls through explicit service interfaces so the chat layer stays vendor-agnostic.

**Tech Stack:** Python 3.12, Django, Django REST Framework, Celery, Redis, MySQL, Qdrant, LangChain, httpx, pytest, pytest-django, python-dotenv or django-environ, drf-spectacular optional later

---

## File Map

### Create

- `backend/manage.py`
- `backend/app/__init__.py`
- `backend/app/asgi.py`
- `backend/app/wsgi.py`
- `backend/app/urls.py`
- `backend/app/celery.py`
- `backend/app/settings/__init__.py`
- `backend/app/settings/base.py`
- `backend/app/settings/local.py`
- `backend/app/settings/docker.py`
- `backend/apps/__init__.py`
- `backend/apps/core/apps.py`
- `backend/apps/core/api/views.py`
- `backend/apps/core/api/urls.py`
- `backend/apps/core/config/env.py`
- `backend/apps/core/exceptions/handlers.py`
- `backend/apps/core/responses/builders.py`
- `backend/apps/documents/apps.py`
- `backend/apps/documents/models.py`
- `backend/apps/documents/serializers.py`
- `backend/apps/documents/views.py`
- `backend/apps/documents/urls.py`
- `backend/apps/documents/services/storage.py`
- `backend/apps/documents/services/upload_service.py`
- `backend/apps/chat/apps.py`
- `backend/apps/chat/models.py`
- `backend/apps/chat/serializers.py`
- `backend/apps/chat/views.py`
- `backend/apps/chat/urls.py`
- `backend/apps/chat/services/conversation_service.py`
- `backend/apps/chat/services/message_service.py`
- `backend/apps/llm/apps.py`
- `backend/apps/llm/interfaces/base.py`
- `backend/apps/llm/clients/gemini.py`
- `backend/apps/llm/clients/ollama.py`
- `backend/apps/llm/clients/mock.py`
- `backend/apps/llm/services/provider_factory.py`
- `backend/apps/llm/services/completion_service.py`
- `backend/apps/retrieval/apps.py`
- `backend/apps/retrieval/services/normalization_service.py`
- `backend/apps/retrieval/services/chunking_service.py`
- `backend/apps/retrieval/services/indexing_service.py`
- `backend/apps/retrieval/services/search_service.py`
- `backend/apps/retrieval/services/summarization_service.py`
- `backend/apps/retrieval/vectorstores/qdrant_store.py`
- `backend/apps/retrieval/langchain/pipelines.py`
- `backend/apps/jobs/apps.py`
- `backend/apps/jobs/tasks/document_tasks.py`
- `backend/apps/jobs/tasks/conversation_tasks.py`
- `backend/apps/mock_data/seeders.py`
- `backend/tests/conftest.py`
- `backend/tests/test_health_api.py`
- `backend/tests/documents/test_document_upload_api.py`
- `backend/tests/documents/test_document_status_api.py`
- `backend/tests/chat/test_conversation_api.py`
- `backend/tests/chat/test_message_api.py`
- `backend/tests/llm/test_provider_factory.py`
- `backend/tests/retrieval/test_normalization_service.py`
- `backend/tests/retrieval/test_search_service.py`
- `backend/tests/jobs/test_document_tasks.py`
- `backend/requirements/base.txt`
- `backend/requirements/dev.txt`
- `backend/.env.example`
- `backend/docker-compose.yml`
- `backend/README.md`

### Modify

- `docs/superpowers/specs/2026-03-30-smartdocsai-backend-design.md`
  - only if implementation uncovers a material design mismatch

## Chunk 1: Bootstrap And Runtime

### Task 1: Add dependencies and environment template

**Files:**
- Create: `backend/requirements/base.txt`
- Create: `backend/requirements/dev.txt`
- Create: `backend/.env.example`
- Test: `backend/README.md`

- [ ] **Step 1: Add dependency manifests**

```text
Django
djangorestframework
mysqlclient
celery
redis
qdrant-client
langchain
langchain-qdrant
httpx
pytest
pytest-django
```

- [ ] **Step 2: Add `.env.example` with MySQL, Redis, Qdrant, Gemini, Ollama, and media settings**

- [ ] **Step 3: Verify the files are coherent**

Run: `rg "DJANGO_SETTINGS_MODULE|QDRANT_URL|OLLAMA_BASE_URL" backend`

Expected: required env vars are present in the new files

- [ ] **Step 4: Commit**

```bash
git add backend/requirements backend/.env.example backend/README.md
git commit -m "build: add backend dependencies and env template"
```

### Task 2: Scaffold Django project, split settings, and Celery app

**Files:**
- Create: `backend/manage.py`
- Create: `backend/app/__init__.py`
- Create: `backend/app/asgi.py`
- Create: `backend/app/wsgi.py`
- Create: `backend/app/urls.py`
- Create: `backend/app/celery.py`
- Create: `backend/app/settings/__init__.py`
- Create: `backend/app/settings/base.py`
- Create: `backend/app/settings/local.py`
- Create: `backend/app/settings/docker.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Write the failing settings smoke test**

```python
def test_django_settings_load(settings):
    assert "rest_framework" in settings.INSTALLED_APPS
    assert settings.ROOT_URLCONF == "app.urls"
```

- [ ] **Step 2: Run the smoke test to verify failure**

Run: `cd backend; pytest tests/conftest.py -v`

Expected: FAIL because the Django project files do not exist yet

- [ ] **Step 3: Create the Django project with split settings and Celery wiring**

- [ ] **Step 4: Run the smoke test again**

Run: `cd backend; pytest tests/conftest.py -v`

Expected: PASS and Django settings import cleanly

- [ ] **Step 5: Commit**

```bash
git add backend/manage.py backend/app backend/tests/conftest.py
git commit -m "build: scaffold django project settings and celery app"
```

### Task 3: Add Docker Compose runtime with optional MySQL container

**Files:**
- Create: `backend/docker-compose.yml`
- Modify: `backend/.env.example`
- Modify: `backend/README.md`

- [ ] **Step 1: Add Compose services for `web`, `worker`, `redis`, `qdrant`, and profiled `mysql`**

- [ ] **Step 2: Make web and worker read the same `.env`**

- [ ] **Step 3: Validate the Compose file**

Run: `cd backend; docker compose config`

Expected: merged Compose config renders without syntax errors

- [ ] **Step 4: Commit**

```bash
git add backend/docker-compose.yml backend/.env.example backend/README.md
git commit -m "build: add compose runtime for backend services"
```

## Chunk 2: Core, Models, And Read APIs

### Task 4: Add core app, shared response helpers, and health endpoint

**Files:**
- Create: `backend/apps/core/apps.py`
- Create: `backend/apps/core/api/views.py`
- Create: `backend/apps/core/api/urls.py`
- Create: `backend/apps/core/config/env.py`
- Create: `backend/apps/core/exceptions/handlers.py`
- Create: `backend/apps/core/responses/builders.py`
- Modify: `backend/app/urls.py`
- Modify: `backend/app/settings/base.py`
- Test: `backend/tests/test_health_api.py`

- [ ] **Step 1: Write the failing health API test**

```python
def test_health_endpoint_returns_dependency_flags(api_client):
    response = api_client.get("/api/health/")
    assert response.status_code == 200
    assert "mysql" in response.json()["data"]["services"]
```

- [ ] **Step 2: Run the health test to verify failure**

Run: `cd backend; pytest tests/test_health_api.py -v`

Expected: FAIL with missing route or missing app import

- [ ] **Step 3: Implement response helpers and health view**

- [ ] **Step 4: Register core app and API routes**

- [ ] **Step 5: Run the health test again**

Run: `cd backend; pytest tests/test_health_api.py -v`

Expected: PASS with a stable response shape

- [ ] **Step 6: Commit**

```bash
git add backend/apps/core backend/app/urls.py backend/app/settings/base.py backend/tests/test_health_api.py
git commit -m "feat: add core health endpoint and shared api helpers"
```

### Task 5: Add document, conversation, join, message, and index models

**Files:**
- Create: `backend/apps/documents/apps.py`
- Create: `backend/apps/documents/models.py`
- Create: `backend/apps/chat/apps.py`
- Create: `backend/apps/chat/models.py`
- Modify: `backend/app/settings/base.py`
- Test: `backend/tests/chat/test_conversation_api.py`
- Test: `backend/tests/chat/test_message_api.py`
- Test: `backend/tests/documents/test_document_status_api.py`

- [ ] **Step 1: Write failing persistence tests for relationships and status fields**

- [ ] **Step 2: Run the model tests to verify failure**

Run: `cd backend; pytest tests/chat/test_conversation_api.py tests/chat/test_message_api.py tests/documents/test_document_status_api.py -v`

Expected: FAIL because models are not defined

- [ ] **Step 3: Implement the models with explicit status enums**

- [ ] **Step 4: Generate and inspect migrations**

Run: `cd backend; python manage.py makemigrations`

Expected: migration files created for `documents` and `chat`

- [ ] **Step 5: Run the persistence tests again**

Run: `cd backend; pytest tests/chat/test_conversation_api.py tests/chat/test_message_api.py tests/documents/test_document_status_api.py -v`

Expected: PASS on model creation and relationship assertions

- [ ] **Step 6: Commit**

```bash
git add backend/apps/documents backend/apps/chat backend/app/settings/base.py backend/tests/chat backend/tests/documents
git add backend/apps/documents/migrations backend/apps/chat/migrations
git commit -m "feat: add document and chat persistence models"
```

### Task 6: Add serializers and list/detail/status endpoints

**Files:**
- Create: `backend/apps/documents/serializers.py`
- Create: `backend/apps/documents/views.py`
- Create: `backend/apps/documents/urls.py`
- Create: `backend/apps/chat/serializers.py`
- Create: `backend/apps/chat/views.py`
- Create: `backend/apps/chat/urls.py`
- Modify: `backend/app/urls.py`
- Test: `backend/tests/documents/test_document_status_api.py`
- Test: `backend/tests/chat/test_conversation_api.py`

- [ ] **Step 1: Write failing API tests for list, detail, and status routes**

- [ ] **Step 2: Run the route tests to verify failure**

Run: `cd backend; pytest tests/documents/test_document_status_api.py tests/chat/test_conversation_api.py -v`

Expected: FAIL with missing serializers or routes

- [ ] **Step 3: Implement serializers and minimal DRF views**

- [ ] **Step 4: Register routes under `/api/documents/` and `/api/conversations/`**

- [ ] **Step 5: Run the route tests again**

Run: `cd backend; pytest tests/documents/test_document_status_api.py tests/chat/test_conversation_api.py -v`

Expected: PASS with stable response payloads

- [ ] **Step 6: Commit**

```bash
git add backend/apps/documents backend/apps/chat backend/app/urls.py backend/tests/documents backend/tests/chat
git commit -m "feat: add baseline document and conversation apis"
```

## Chunk 3: Upload, Background Jobs, And Retrieval

### Task 7: Add multi-file upload service and upload endpoint

**Files:**
- Create: `backend/apps/documents/services/storage.py`
- Create: `backend/apps/documents/services/upload_service.py`
- Modify: `backend/apps/documents/serializers.py`
- Modify: `backend/apps/documents/views.py`
- Test: `backend/tests/documents/test_document_upload_api.py`

- [ ] **Step 1: Write the failing multi-file upload API test**

```python
def test_upload_endpoint_accepts_multiple_files(api_client, tmp_path):
    response = api_client.post("/api/documents/upload/", {"files": [file_a, file_b]}, format="multipart")
    assert response.status_code == 201
    assert len(response.json()["data"]["documents"]) == 2
```

- [ ] **Step 2: Run the upload test to verify failure**

Run: `cd backend; pytest tests/documents/test_document_upload_api.py -v`

Expected: FAIL because upload endpoint and service do not exist

- [ ] **Step 3: Implement storage and upload service boundaries**

- [ ] **Step 4: Add the DRF multipart endpoint**

- [ ] **Step 5: Run the upload test again**

Run: `cd backend; pytest tests/documents/test_document_upload_api.py -v`

Expected: PASS and uploaded documents are returned with `processing_status=uploaded`

- [ ] **Step 6: Commit**

```bash
git add backend/apps/documents backend/tests/documents/test_document_upload_api.py
git commit -m "feat: add multi-file document upload api"
```

### Task 8: Add Celery document processing task and enqueue on upload

**Files:**
- Create: `backend/apps/jobs/apps.py`
- Create: `backend/apps/jobs/tasks/document_tasks.py`
- Modify: `backend/apps/documents/services/upload_service.py`
- Modify: `backend/app/settings/base.py`
- Test: `backend/tests/jobs/test_document_tasks.py`

- [ ] **Step 1: Write the failing enqueue behavior test**

- [ ] **Step 2: Run the jobs test to verify failure**

Run: `cd backend; pytest tests/jobs/test_document_tasks.py -v`

Expected: FAIL because task import path does not exist

- [ ] **Step 3: Implement `process_document` Celery task stub**

- [ ] **Step 4: Call the task from the upload service after document creation**

- [ ] **Step 5: Run the jobs test again**

Run: `cd backend; pytest tests/jobs/test_document_tasks.py -v`

Expected: PASS and task dispatch is asserted

- [ ] **Step 6: Commit**

```bash
git add backend/apps/jobs backend/apps/documents/services/upload_service.py backend/app/settings/base.py backend/tests/jobs/test_document_tasks.py
git commit -m "feat: enqueue document processing background jobs"
```

### Task 9: Implement normalization and chunking service boundaries

**Files:**
- Create: `backend/apps/retrieval/apps.py`
- Create: `backend/apps/retrieval/services/normalization_service.py`
- Create: `backend/apps/retrieval/services/chunking_service.py`
- Create: `backend/apps/retrieval/langchain/pipelines.py`
- Test: `backend/tests/retrieval/test_normalization_service.py`

- [ ] **Step 1: Write the failing normalization service test**

```python
def test_normalization_collapses_extra_whitespace():
    normalized = service.normalize_text("A\\n\\n\\nB")
    assert normalized == "A\\n\\nB"
```

- [ ] **Step 2: Run the normalization test to verify failure**

Run: `cd backend; pytest tests/retrieval/test_normalization_service.py -v`

Expected: FAIL because the service module is missing

- [ ] **Step 3: Implement the normalization service and chunking service**

- [ ] **Step 4: Add pipeline glue for `normalize -> chunk`**

- [ ] **Step 5: Run the normalization test again**

Run: `cd backend; pytest tests/retrieval/test_normalization_service.py -v`

Expected: PASS with deterministic normalized output

- [ ] **Step 6: Commit**

```bash
git add backend/apps/retrieval backend/tests/retrieval/test_normalization_service.py
git commit -m "feat: add retrieval normalization and chunking services"
```

### Task 10: Implement Qdrant vector store adapter and search service skeleton

**Files:**
- Create: `backend/apps/retrieval/vectorstores/qdrant_store.py`
- Create: `backend/apps/retrieval/services/indexing_service.py`
- Create: `backend/apps/retrieval/services/search_service.py`
- Modify: `backend/apps/retrieval/langchain/pipelines.py`
- Test: `backend/tests/retrieval/test_search_service.py`

- [ ] **Step 1: Write the failing search service interface test**

- [ ] **Step 2: Run the search test to verify failure**

Run: `cd backend; pytest tests/retrieval/test_search_service.py -v`

Expected: FAIL because vector store modules do not exist

- [ ] **Step 3: Implement the Qdrant adapter and service interfaces**

- [ ] **Step 4: Connect indexing pipeline to `chunk -> upsert`**

- [ ] **Step 5: Run the search test again**

Run: `cd backend; pytest tests/retrieval/test_search_service.py -v`

Expected: PASS with mocked Qdrant client interactions

- [ ] **Step 6: Commit**

```bash
git add backend/apps/retrieval backend/tests/retrieval/test_search_service.py
git commit -m "feat: add qdrant vector store and search service skeleton"
```

### Task 11: Add summarization service and complete document processing flow

**Files:**
- Create: `backend/apps/retrieval/services/summarization_service.py`
- Modify: `backend/apps/jobs/tasks/document_tasks.py`
- Modify: `backend/apps/documents/models.py`
- Test: `backend/tests/jobs/test_document_tasks.py`

- [ ] **Step 1: Extend the jobs test with final status expectations**

- [ ] **Step 2: Run the jobs test to verify failure**

Run: `cd backend; pytest tests/jobs/test_document_tasks.py -v`

Expected: FAIL because summarization and status updates are incomplete

- [ ] **Step 3: Implement summarization boundary and task orchestration**

- [ ] **Step 4: Persist failure handling in the task**

- [ ] **Step 5: Run the jobs test again**

Run: `cd backend; pytest tests/jobs/test_document_tasks.py -v`

Expected: PASS for both success and failure state transitions

- [ ] **Step 6: Commit**

```bash
git add backend/apps/retrieval/services/summarization_service.py backend/apps/jobs/tasks/document_tasks.py backend/apps/documents/models.py backend/tests/jobs/test_document_tasks.py
git commit -m "feat: finalize document processing and summary generation flow"
```

## Chunk 4: Providers, Conversations, Messages, And DX

### Task 12: Add provider interface, Gemini/Ollama/mock clients, and provider factory

**Files:**
- Create: `backend/apps/llm/apps.py`
- Create: `backend/apps/llm/interfaces/base.py`
- Create: `backend/apps/llm/clients/gemini.py`
- Create: `backend/apps/llm/clients/ollama.py`
- Create: `backend/apps/llm/clients/mock.py`
- Create: `backend/apps/llm/services/provider_factory.py`
- Create: `backend/apps/llm/services/completion_service.py`
- Test: `backend/tests/llm/test_provider_factory.py`

- [ ] **Step 1: Write the failing provider factory tests**

```python
def test_factory_returns_mock_when_gemini_config_missing(settings):
    client = factory.build("gemini")
    assert client.provider_name == "mock"
```

- [ ] **Step 2: Run the provider tests to verify failure**

Run: `cd backend; pytest tests/llm/test_provider_factory.py -v`

Expected: FAIL because the factory and clients do not exist

- [ ] **Step 3: Implement the provider interface and concrete clients**

- [ ] **Step 4: Implement environment-driven provider resolution**

- [ ] **Step 5: Run the provider tests again**

Run: `cd backend; pytest tests/llm/test_provider_factory.py -v`

Expected: PASS for Gemini, Ollama, and mock fallback cases

- [ ] **Step 6: Commit**

```bash
git add backend/apps/llm backend/tests/llm/test_provider_factory.py
git commit -m "feat: add llm provider interfaces and fallback factory"
```

### Task 13: Add provider status and test endpoints

**Files:**
- Modify: `backend/apps/core/api/views.py`
- Modify: `backend/apps/core/api/urls.py`
- Modify: `backend/apps/llm/services/provider_factory.py`
- Test: `backend/tests/test_health_api.py`

- [ ] **Step 1: Add failing tests for `/api/providers/` and `/api/providers/test/`**

- [ ] **Step 2: Run the provider endpoint tests to verify failure**

Run: `cd backend; pytest tests/test_health_api.py -v`

Expected: FAIL because the provider routes are not defined

- [ ] **Step 3: Implement provider readiness views**

- [ ] **Step 4: Add lightweight provider test behavior**

- [ ] **Step 5: Run the provider endpoint tests again**

Run: `cd backend; pytest tests/test_health_api.py -v`

Expected: PASS with stable provider readiness payloads

- [ ] **Step 6: Commit**

```bash
git add backend/apps/core/api backend/apps/llm/services/provider_factory.py backend/tests/test_health_api.py
git commit -m "feat: add provider status and test endpoints"
```

### Task 14: Add conversation creation service and preparation task

**Files:**
- Create: `backend/apps/chat/services/conversation_service.py`
- Create: `backend/apps/jobs/tasks/conversation_tasks.py`
- Modify: `backend/apps/chat/views.py`
- Modify: `backend/apps/chat/serializers.py`
- Test: `backend/tests/chat/test_conversation_api.py`

- [ ] **Step 1: Extend the conversation API test for creation with document IDs**

- [ ] **Step 2: Run the conversation API tests to verify failure**

Run: `cd backend; pytest tests/chat/test_conversation_api.py -v`

Expected: FAIL because create flow and task enqueue logic are missing

- [ ] **Step 3: Implement conversation creation service**

- [ ] **Step 4: Implement `prepare_conversation` task dispatch**

- [ ] **Step 5: Run the conversation API tests again**

Run: `cd backend; pytest tests/chat/test_conversation_api.py -v`

Expected: PASS for conversation creation and status transitions

- [ ] **Step 6: Commit**

```bash
git add backend/apps/chat backend/apps/jobs/tasks/conversation_tasks.py backend/tests/chat/test_conversation_api.py
git commit -m "feat: add conversation creation and preparation flow"
```

### Task 15: Add message service, history endpoint, and chat completion flow

**Files:**
- Create: `backend/apps/chat/services/message_service.py`
- Modify: `backend/apps/chat/views.py`
- Modify: `backend/apps/chat/serializers.py`
- Modify: `backend/apps/retrieval/services/search_service.py`
- Modify: `backend/apps/llm/services/completion_service.py`
- Test: `backend/tests/chat/test_message_api.py`

- [ ] **Step 1: Write the failing history and send-message tests**

- [ ] **Step 2: Run the message API tests to verify failure**

Run: `cd backend; pytest tests/chat/test_message_api.py -v`

Expected: FAIL because history and send-message flows are incomplete

- [ ] **Step 3: Implement the message service orchestration**

- [ ] **Step 4: Add guard behavior for `preparing` conversations**

- [ ] **Step 5: Run the message API tests again**

Run: `cd backend; pytest tests/chat/test_message_api.py -v`

Expected: PASS for history retrieval, ready conversation chat, and non-ready guard behavior

- [ ] **Step 6: Commit**

```bash
git add backend/apps/chat backend/apps/retrieval/services/search_service.py backend/apps/llm/services/completion_service.py backend/tests/chat/test_message_api.py
git commit -m "feat: add message history and chat completion flow"
```

### Task 16: Add mock data seeders and backend runbook

**Files:**
- Create: `backend/apps/mock_data/seeders.py`
- Create: `backend/README.md`
- Modify: `backend/tests/conftest.py`
- Test: `backend/tests/conftest.py`

- [ ] **Step 1: Add the failing seed smoke test**

- [ ] **Step 2: Run the seed smoke test to verify failure**

Run: `cd backend; pytest tests/conftest.py -v`

Expected: FAIL because seed helpers do not exist

- [ ] **Step 3: Implement sample data helpers and README setup docs**

- [ ] **Step 4: Document local, docker, worker, and test commands**

- [ ] **Step 5: Run the seed smoke test again**

Run: `cd backend; pytest tests/conftest.py -v`

Expected: PASS and README covers the supported run modes

- [ ] **Step 6: Commit**

```bash
git add backend/apps/mock_data backend/tests/conftest.py backend/README.md
git commit -m "docs: add mock data seeders and backend runbook"
```

## Chunk 5: Final Verification

### Task 17: Run the full backend suite and smoke-check Django commands

**Files:**
- Test: `backend/tests/test_health_api.py`
- Test: `backend/tests/documents/test_document_upload_api.py`
- Test: `backend/tests/documents/test_document_status_api.py`
- Test: `backend/tests/chat/test_conversation_api.py`
- Test: `backend/tests/chat/test_message_api.py`
- Test: `backend/tests/llm/test_provider_factory.py`
- Test: `backend/tests/retrieval/test_normalization_service.py`
- Test: `backend/tests/retrieval/test_search_service.py`
- Test: `backend/tests/jobs/test_document_tasks.py`

- [ ] **Step 1: Run the full test suite**

Run: `cd backend; pytest -v`

Expected: PASS for all backend tests

- [ ] **Step 2: Run Django system checks**

Run: `cd backend; python manage.py check`

Expected: `System check identified no issues`

- [ ] **Step 3: Validate migrations are complete**

Run: `cd backend; python manage.py makemigrations --check --dry-run`

Expected: no changes detected

- [ ] **Step 4: Validate Docker Compose configuration**

Run: `cd backend; docker compose config`

Expected: config renders successfully

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "test: verify backend scaffold end to end"
```

## Notes For The Implementer

- Keep view classes thin and push orchestration into services.
- Do not let `chat` import provider SDKs directly.
- Do not let document upload perform normalization inline.
- Treat Qdrant integration as a replaceable adapter, not an app-wide dependency.
- If async ORM usage becomes awkward, keep database writes synchronous inside services and restrict async to network-bound calls.
- Keep LangChain as a thin boundary around chunking, indexing, and search helpers; do not introduce agent abstractions in this phase.
