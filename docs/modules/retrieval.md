# Retrieval Module

## Purpose

`retrieval` is the preprocessing and search layer between uploaded documents and chat completion.

Its job is:

`document content -> normalization -> chunking -> vector indexing -> search -> context for llm`

## Main Files

- `backend/apps/retrieval/services/normalization_service.py`
  - cleans raw text into a stable normalized form
- `backend/apps/retrieval/services/chunking_service.py`
  - splits normalized text into chunks using LangChain text splitters
- `backend/apps/retrieval/services/indexing_service.py`
  - updates `DocumentIndex` metadata after vector upsert
- `backend/apps/retrieval/services/search_service.py`
  - used by chat to search relevant chunks
- `backend/apps/retrieval/services/summarization_service.py`
  - creates a short summary after indexing
- `backend/apps/retrieval/vectorstores/qdrant_store.py`
  - adapter boundary for vector storage/search
- `backend/apps/retrieval/langchain/pipelines.py`
  - orchestration glue for normalization, chunking, indexing, and summary
- `backend/apps/retrieval/views.py`
  - retrieval debug endpoint
- `backend/apps/retrieval/urls.py`
  - route for `/api/retrieval/search/`

## Current Behavior

### Normalization

- collapses repeated whitespace
- reduces excessive blank lines
- preserves paragraph-ish separation
- returns a `NormalizedDocument` payload

### Chunking

- uses `RecursiveCharacterTextSplitter`
- produces chunk payloads with metadata

### Vector Store

- current `QdrantStore` is a scaffold adapter
- it returns index metadata and mockable search results
- the adapter boundary exists so real Qdrant operations can replace the stub later

### Summarization

- currently generates a short summary from the first chunk

## Endpoint

- `GET /api/retrieval/search/?query=...&document_ids=1&document_ids=2`

Useful for:

- manual retrieval checks
- FE/backend debugging
- validating search shape independently of chat

## Dependencies

- depends on `documents` for index metadata
- depends on LangChain splitter utilities
- is used by `jobs` during background processing
- is used by `chat` during message handling

## What To Extend Next

- replace stub vector adapter with real Qdrant collection operations
- add real embedding generation
- add metadata filters per document or conversation
- improve summaries beyond first-chunk truncation
