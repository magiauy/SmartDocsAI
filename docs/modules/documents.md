# Documents Module

## Purpose

`documents` manages uploaded file metadata and the API surface around document creation and status tracking.

This module is the entry point for the document flow:

`upload file -> persist metadata -> queue background processing -> expose status to FE`

## Main Files

- `backend/apps/documents/models.py`
  - `Document`
  - `DocumentIndex`
- `backend/apps/documents/serializers.py`
  - upload, detail, and status serializers
- `backend/apps/documents/views.py`
  - list/detail/delete/upload/status/index endpoints
- `backend/apps/documents/urls.py`
  - routes under `/api/documents/`
- `backend/apps/documents/services/storage.py`
  - physical file save helper
- `backend/apps/documents/services/upload_service.py`
  - creates `Document` rows and enqueues background jobs

## Models

### Document

Stores:

- title
- original filename
- saved file path
- mime type
- size
- source
- processing status
- summary status
- generated summary
- error message

### DocumentIndex

Stores index metadata only:

- vector collection name
- chunk count
- index status

## Endpoints

- `GET /api/documents/`
- `POST /api/documents/upload/`
- `GET /api/documents/{id}/`
- `DELETE /api/documents/{id}/`
- `GET /api/documents/{id}/status/`
- `POST /api/documents/{id}/index/`
- `POST /api/documents/index/bulk/`

## Current Flow

1. `DocumentUploadView` receives one or many files
2. `UploadService` saves files through `StorageService`
3. `Document` rows are created with `uploaded/pending` state
4. `jobs.tasks.document_tasks.process_document.delay()` is queued
5. FE polls status endpoints until documents become `indexed` or `failed`

## Dependencies

- depends on `jobs` for async processing
- feeds `retrieval` via the background pipeline
- is referenced by `chat` through many-to-many attachment

## What To Extend Next

- replace simple file save with pluggable storage backends
- validate allowed file types and size limits
- support real extraction for PDF/DOCX instead of plain-text fallback
- add delete cleanup for stored files and vector records
