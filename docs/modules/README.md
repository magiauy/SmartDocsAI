# SmartDocsAI Module Docs

This folder documents the backend modules that were scaffolded in `backend/apps`.

## Modules

- `core`
  - shared API response shape, health endpoints, provider readiness endpoints, and DRF exception mapping
- `documents`
  - uploaded file metadata, upload endpoints, document status endpoints, and file storage helpers
- `chat`
  - conversations, attached documents, persisted messages, and message orchestration
- `llm`
  - provider interface, Gemini/Ollama/mock adapters, and provider resolution
- `retrieval`
  - normalization, chunking, indexing, vector search, summarization, and retrieval debug endpoint
- `jobs`
  - background task entrypoints for document preparation and conversation preparation
- `demo`
  - browser demo page served by Django for testing the backend flow
- `mock_data`
  - seed helpers for local development and quick demos

## Reading Order

1. `core.md`
2. `documents.md`
3. `retrieval.md`
4. `llm.md`
5. `chat.md`
6. `jobs.md`
7. `demo.md`
8. `mock-data.md`

That order follows the request flow most closely:

`request -> core routing -> documents upload -> retrieval prep -> llm -> chat persistence -> jobs/demo`
