# Jobs Module

## Purpose

`jobs` contains the Celery task entrypoints that keep long-running work out of request-response handling.

This is the module that makes the backend non-blocking at the workflow level.

## Main Files

- `backend/apps/jobs/tasks/document_tasks.py`
  - `process_document`
- `backend/apps/jobs/tasks/conversation_tasks.py`
  - `prepare_conversation`

## Current Tasks

### process_document(document_id)

Responsibilities:

- move document to `processing`
- call retrieval pipeline
- update `DocumentIndex`
- write summary to `Document`
- mark success or failure state

### prepare_conversation(conversation_id)

Responsibilities:

- check whether attached documents are ready
- create a bootstrap assistant message when summaries exist
- move conversation to `ready` or leave it `preparing`

## Dependencies

- depends on `documents`
- depends on `chat`
- depends on `retrieval`
- runs under Celery/Redis

## Operational Notes

- if `web` starts before MySQL is ready, the server can log a transient DB connection error
- the worker itself is already wired and registers the document/conversation tasks
- current Docker setup runs Celery as root inside the container, which is fine for local dev but not ideal for production

## What To Extend Next

- add retry policies and structured failure handling
- separate indexing and summarization into smaller task chains if needed
- expose task progress more explicitly to FE
