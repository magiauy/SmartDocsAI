# SmartDocsAI Backend Design

Date: 2026-03-30
Status: Approved in brainstorming
Scope: Backend project initialization only

## 1. Goal

Initialize a Django backend for SmartDocsAI with:

- Django + Django REST Framework
- MySQL as the transactional database
- Qdrant as the vector database
- LangChain-based retrieval boundary
- LLM interface for Gemini and Ollama
- Mock data and fallback behavior
- Background processing for normalization, indexing, and summarization
- Conversation history persistence
- Multi-file document upload
- Async-safe runtime boundaries so long-running work does not block request handling

This phase only establishes the project skeleton, interfaces, utilities, and baseline API surface. It does not implement full OCR, production auth, or production-grade retrieval quality.

## 2. Constraints And Decisions

- Framework: Django + DRF
- API style: JSON REST API
- Auth: none in this phase
- Document support: multi-file upload
- Conversation support: one conversation may reference many documents
- Chat history: persisted in MySQL
- Background work: normalization, chunking, vector indexing, and summary generation
- Retrieval order: normalize -> store/search vector DB -> build context -> call LLM interface
- Provider strategy: real Gemini/Ollama adapters with mock fallback when config is missing
- Runtime strategy: ASGI + async HTTP clients + background worker so request threads are not blocked
- Database strategy: support both MySQL in Docker and external MySQL via environment configuration

## 3. Recommended Architecture

Use a modular monolith.

This keeps deployment simple while giving clear boundaries between upload, chat, retrieval, and provider logic. The system remains a single Django project, but domain responsibilities are split into focused apps and services.

### 3.1 Project Layout

```text
backend/
  manage.py
  app/
    settings/
      base.py
      local.py
      docker.py
    asgi.py
    urls.py
    celery.py
  apps/
    core/
      health/
      api/
      exceptions/
      responses/
      config/
    documents/
      models.py
      serializers.py
      views.py
      urls.py
      services/
        storage.py
        upload_service.py
    chat/
      models.py
      serializers.py
      views.py
      urls.py
      services/
        conversation_service.py
        message_service.py
    llm/
      interfaces/
        base.py
      clients/
        gemini.py
        ollama.py
        mock.py
      services/
        provider_factory.py
        completion_service.py
    retrieval/
      services/
        normalization_service.py
        chunking_service.py
        indexing_service.py
        search_service.py
        summarization_service.py
      vectorstores/
        qdrant_store.py
      langchain/
        pipelines.py
    jobs/
      tasks/
        document_tasks.py
        conversation_tasks.py
    mock_data/
      seeders.py
  media/
  docs/
  requirements/
```

### 3.2 Responsibilities By Domain

- `core`
  - settings, env parsing, health checks, shared API responses, exception mapping
- `documents`
  - document metadata, file upload, file storage abstraction, document status APIs
- `chat`
  - conversations, messages, history APIs, conversation-document relationships
- `llm`
  - LLM interface, provider selection, real provider clients, mock fallback
- `retrieval`
  - normalization, chunk preparation, indexing, vector search, summary generation
- `jobs`
  - Celery tasks and orchestration for background processing
- `mock_data`
  - seed utilities for local/dev/demo data

## 4. Runtime Model

### 4.1 Web Runtime

- Django runs under ASGI
- DRF handles REST endpoints
- Outbound provider calls use an async HTTP client
- The API process should return quickly and avoid performing normalization or indexing inline

### 4.2 Background Runtime

Use Celery + Redis for queue and worker processing.

Reason:

- Upload and conversation preparation should not block request handling
- Normalization, chunking, indexing, and summarization are background responsibilities
- The queue boundary is cleaner than relying on request threads for long-running work

### 4.3 Persistence

- MySQL stores transactional data and history
- Qdrant stores vectors and searchable chunk metadata
- Files are stored in Django media storage for now

## 5. Core User Flows

### 5.1 Upload Documents

1. User uploads one or more files
2. API stores files and document metadata in MySQL
3. API returns immediately with `processing_status=uploaded`
4. Background task starts:
   - normalize content
   - create chunks
   - upsert chunks to Qdrant
   - generate summary
5. Document status becomes `indexed` or `failed`

### 5.2 Create Conversation

1. User creates a conversation with one or more `document_ids`
2. Conversation is created in MySQL
3. If any attached document is not ready, conversation starts as `preparing`
4. Background task checks document readiness and can generate a bootstrap assistant summary message
5. When preparation completes, conversation becomes `ready`

### 5.3 Ask A Question

1. User posts a message to a conversation
2. If conversation is `preparing`, API returns a non-ready response and current state
3. If conversation is `ready`:
   - save user message
   - run retrieval search against Qdrant
   - build prompt context
   - call selected LLM interface
   - save assistant message
   - return answer plus retrieval metadata

## 6. Data Model

### 6.1 Document

Stores uploaded file metadata.

Suggested fields:

- `id`
- `title`
- `original_filename`
- `file_path`
- `mime_type`
- `size_bytes`
- `source`
- `status`
- `processing_status`
- `summary_status`
- `summary`
- `error_message`
- `created_at`
- `updated_at`

Suggested statuses:

- `uploaded`
- `processing`
- `indexed`
- `failed`

### 6.2 DocumentIndex

Stores index metadata only, not vectors.

Suggested fields:

- `id`
- `document`
- `vector_collection`
- `chunk_count`
- `index_status`
- `last_indexed_at`
- `created_at`
- `updated_at`

### 6.3 Conversation

Suggested fields:

- `id`
- `title`
- `provider`
- `model`
- `system_prompt`
- `status`
- `created_at`
- `updated_at`

Suggested statuses:

- `preparing`
- `ready`
- `failed`

### 6.4 ConversationDocument

Many-to-many join table between conversations and documents.

Suggested fields:

- `id`
- `conversation`
- `document`
- `created_at`

### 6.5 Message

Suggested fields:

- `id`
- `conversation`
- `role`
- `content`
- `provider`
- `model`
- `tokens_input`
- `tokens_output`
- `latency_ms`
- `metadata_json`
- `created_at`

Suggested roles:

- `system`
- `assistant`
- `user`

## 7. API Surface

Base prefix: `/api`

### 7.1 Health

- `GET /api/health/`
  - checks application, MySQL, Redis, and Qdrant reachability

### 7.2 Providers

- `GET /api/providers/`
  - list supported providers and configuration readiness
- `POST /api/providers/test/`
  - test provider connectivity or return mock-capable status

### 7.3 Documents

- `GET /api/documents/`
  - list documents
- `POST /api/documents/upload/`
  - upload one or many files
- `GET /api/documents/{id}/`
  - document detail
- `DELETE /api/documents/{id}/`
  - delete metadata and optionally stored file
- `GET /api/documents/{id}/status/`
  - processing/indexing status
- `POST /api/documents/{id}/index/`
  - manually trigger indexing job
- `POST /api/documents/index/bulk/`
  - trigger indexing for multiple documents

### 7.4 Conversations

- `GET /api/conversations/`
  - list conversations
- `POST /api/conversations/`
  - create conversation and attach `document_ids`
- `GET /api/conversations/{id}/`
  - conversation detail
- `GET /api/conversations/{id}/status/`
  - readiness state for FE polling
- `PATCH /api/conversations/{id}/documents/`
  - replace or update attached documents

### 7.5 Messages

- `GET /api/conversations/{id}/messages/`
  - fetch chat history
- `POST /api/conversations/{id}/messages/`
  - send message, retrieve context, call provider, save response

### 7.6 Retrieval Debug

- `GET /api/retrieval/search/`
  - debug endpoint to test vector search against current documents

## 8. Background Processing Design

### 8.1 Why Background Jobs Are Required

Normalization, indexing, and summarization should not run inside request-response handling. These steps may involve file IO, parsing, vector operations, network calls, and provider latency. Running them inline would block workers and reduce concurrency.

### 8.2 Background Tasks

Recommended task boundaries:

- `process_document(document_id)`
  - load file
  - normalize text
  - create chunks
  - store vectors in Qdrant
  - generate summary
  - update document statuses
- `prepare_conversation(conversation_id)`
  - verify attached documents are ready
  - create or refresh conversation bootstrap summary message
  - move conversation to `ready` or `failed`

### 8.3 Conversation Bootstrap Message

When a conversation becomes ready, create an assistant message that summarizes the attached documents. This gives the frontend something useful to render immediately and matches the intended product flow: upload first, prepare in the background, then wait for the user’s next question.

## 9. Normalization Design

### 9.1 What Normalization Must Do

Normalization is the preprocessing stage before chunking and indexing. In this scaffold it should:

- load file content or extracted text
- standardize line endings and whitespace
- remove repeated empty blocks
- preserve readable paragraph boundaries
- attach document metadata to the normalized payload
- produce a deterministic text output that downstream chunking can consume

This phase does not need full OCR or advanced PDF extraction quality yet. It only needs a clean service boundary and baseline text normalization flow.

### 9.2 Where The Code Goes

Primary code location:

- `apps/retrieval/services/normalization_service.py`

Supporting code:

- `apps/documents/services/storage.py`
  - file loading helpers
- `apps/retrieval/langchain/pipelines.py`
  - orchestration with chunking/indexing
- `apps/jobs/tasks/document_tasks.py`
  - worker entrypoint that calls normalization

### 9.3 Expected Interface

Suggested service contract:

```python
class NormalizationService:
    async def normalize_document(self, document: Document) -> NormalizedDocument:
        ...
```

The return object should include:

- `document_id`
- `normalized_text`
- `metadata`
- `content_hash`

## 10. Vector Store And Search Design

### 10.1 What Vector Storage Must Do

The vector layer must:

- receive normalized text chunks
- generate or accept embeddings through the chosen embedding pipeline
- upsert chunk vectors into Qdrant
- store chunk metadata for filtering and traceability
- support similarity search by conversation and attached documents

### 10.2 What Search Must Do

Search should:

- accept a user query and target document scope
- perform similarity search in Qdrant
- return top matching chunks with metadata
- provide enough context for prompt building

This scaffold can keep ranking logic simple and focus on stable interfaces.

### 10.3 Where The Code Goes

Primary code locations:

- `apps/retrieval/vectorstores/qdrant_store.py`
- `apps/retrieval/services/indexing_service.py`
- `apps/retrieval/services/search_service.py`
- `apps/retrieval/services/chunking_service.py`

LangChain integration boundary:

- `apps/retrieval/langchain/pipelines.py`

Worker integration:

- `apps/jobs/tasks/document_tasks.py`

### 10.4 Expected Interfaces

Suggested contracts:

```python
class VectorStoreService:
    async def upsert_document(self, document: Document, chunks: list[ChunkPayload]) -> IndexResult:
        ...

    async def search(self, query: str, document_ids: list[int], limit: int = 5) -> list[SearchHit]:
        ...
```

The Qdrant adapter should stay behind this interface so the storage backend can be replaced later without rewriting chat logic.

## 11. LLM Interface Design

### 11.1 What The LLM Layer Must Do

The LLM layer must:

- expose a provider-agnostic completion interface
- support Gemini and Ollama adapters
- select provider by conversation or request config
- support real calls when environment variables are present
- fall back to mock responses when provider config is absent
- return normalized response metadata to the chat layer

### 11.2 Where The Code Goes

Primary code locations:

- `apps/llm/interfaces/base.py`
- `apps/llm/clients/gemini.py`
- `apps/llm/clients/ollama.py`
- `apps/llm/clients/mock.py`
- `apps/llm/services/provider_factory.py`
- `apps/llm/services/completion_service.py`

Chat integration:

- `apps/chat/services/message_service.py`

### 11.3 Expected Interfaces

Suggested contracts:

```python
class LLMClient:
    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        ...
```

The factory should resolve a provider name such as `gemini` or `ollama` and return an adapter implementing `LLMClient`.

### 11.4 Provider Notes

- `GeminiClient`
  - reads API key and model from environment
  - uses async HTTP calls
- `OllamaClient`
  - reads base URL and model from environment
  - uses async HTTP calls to the local or remote Ollama server
- `MockClient`
  - returns deterministic fake answers and metadata
  - used when provider configuration is incomplete

## 12. Prompt And Retrieval Composition

Message handling should follow this order:

1. save user message
2. search vector store using conversation documents
3. build context from top chunks
4. create completion request
5. call provider client
6. save assistant response
7. return answer, citations metadata, and provider info

The chat service should never directly depend on Qdrant SDK or provider-specific APIs. Those dependencies remain behind retrieval and LLM service boundaries.

## 13. Frontend Integration Contract

The frontend will need clear status-driven flows.

### 13.1 Upload Flow

Frontend behavior:

1. call `POST /api/documents/upload/` with multiple files
2. render the returned document list with `processing_status`
3. poll `GET /api/documents/{id}/status/` until document becomes `indexed` or `failed`

### 13.2 Conversation Creation Flow

Frontend behavior:

1. call `POST /api/conversations/` with selected `document_ids`
2. inspect returned `status`
3. if `preparing`, poll `GET /api/conversations/{id}/status/`
4. once `ready`, call `GET /api/conversations/{id}/messages/`
5. render the bootstrap summary message before the user sends the next question

### 13.3 Chat Flow

Frontend behavior:

1. call `POST /api/conversations/{id}/messages/`
2. if conversation is still `preparing`, disable the input or show waiting state
3. if response is successful, append both user and assistant messages to the UI
4. optionally show provider/model/debug metadata in developer mode

### 13.4 FE Error Cases

Frontend should handle:

- document processing failure
- conversation preparation failure
- provider unavailable but mock fallback active
- retrieval returns no relevant chunks

### 13.5 Suggested Response Shape

Keep responses consistent and explicit:

- `success`
- `message`
- `data`
- `errors`

For status endpoints, include:

- `status`
- `processing_status`
- `summary_status`
- `ready_for_chat`
- `error_message`

## 14. Configuration Design

### 14.1 Environment Variables

Core:

- `DEBUG`
- `SECRET_KEY`
- `ALLOWED_HOSTS`

MySQL:

- `DB_ENGINE`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_USE_DOCKER`

Redis/Celery:

- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

Qdrant:

- `QDRANT_URL`
- `QDRANT_API_KEY`
- `QDRANT_COLLECTION`

Gemini:

- `GEMINI_API_KEY`
- `GEMINI_MODEL`

Ollama:

- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`

Storage:

- `MEDIA_ROOT`
- `MEDIA_URL`

### 14.2 Docker Compose Expectations

Compose should support:

- Django web
- Celery worker
- Redis
- Qdrant
- optional MySQL container

The MySQL service should be easy to enable or bypass. The Django config should accept either:

- Docker MySQL host such as `mysql`
- external MySQL host from `.env`

## 15. Mock Data Strategy

Provide seed helpers for:

- sample documents
- sample conversations
- sample messages
- sample provider availability states

Mock data is for local development only and should not replace the persistent data model.

## 16. Testing And Verification Scope

For the initialization phase, cover:

- health endpoint
- multi-file upload API
- conversation creation API
- message history API
- provider factory selection
- mock fallback behavior
- retrieval service interfaces
- status transitions for background jobs

Do not attempt full end-to-end accuracy evaluation in this phase.

## 17. Non-Goals For This Phase

- authentication and authorization
- advanced OCR pipeline
- production-grade document parsing quality
- production deployment hardening
- websocket/SSE streaming
- advanced reranking
- tenant isolation

## 18. Implementation Notes For Next Phase

The implementation phase should prioritize:

1. project bootstrap and settings
2. persistence models and migrations
3. document upload and storage services
4. background queue and worker setup
5. retrieval interfaces and Qdrant integration skeleton
6. LLM provider interfaces and fallback behavior
7. chat endpoints and history persistence
8. mock data and baseline tests

This keeps the architecture stable while limiting scope to project initialization and integration boundaries.
