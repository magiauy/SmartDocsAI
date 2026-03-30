# Chat Module

## Purpose

`chat` owns conversations, attached documents, message history, and the request orchestration for asking questions against prepared document context.

This module is the main consumer of `retrieval` and `llm`.

## Main Files

- `backend/apps/chat/models.py`
  - `Conversation`
  - `ConversationDocument`
  - `Message`
- `backend/apps/chat/serializers.py`
  - serializers for conversation create/detail/status and messages
- `backend/apps/chat/views.py`
  - list/create/detail/status/document-update/message endpoints
- `backend/apps/chat/urls.py`
  - routes under `/api/conversations/`
- `backend/apps/chat/services/conversation_service.py`
  - creates conversations and attaches documents
- `backend/apps/chat/services/message_service.py`
  - saves user messages, calls retrieval, calls llm, saves assistant messages

## Models

### Conversation

Stores:

- title
- provider
- model
- system prompt
- status: `preparing`, `ready`, `failed`

### ConversationDocument

Join table between a conversation and one or more documents.

### Message

Stores:

- role
- content
- provider/model used
- token counts
- latency
- metadata JSON

## Endpoints

- `GET /api/conversations/`
- `POST /api/conversations/`
- `GET /api/conversations/{id}/`
- `GET /api/conversations/{id}/status/`
- `PATCH /api/conversations/{id}/documents/`
- `GET /api/conversations/{id}/messages/`
- `POST /api/conversations/{id}/messages/`

## Current Flow

### Create Conversation

1. FE sends `title`, `provider`, `model`, `document_ids`
2. `ConversationService` creates the row
3. selected documents are attached through `ConversationDocument`
4. `prepare_conversation.delay()` is queued

### Send Message

1. `MessageService` checks conversation status
2. if not `ready`, returns a guard response with `409`
3. if `ready`, saves the user message
4. calls retrieval search using attached documents
5. calls the selected completion service
6. saves the assistant message

## Dependencies

- depends on `documents` for attached file scope
- depends on `retrieval` for search context
- depends on `llm` for completion generation
- depends on `jobs` for async preparation

## What To Extend Next

- improve conversation status transitions and failure reasons
- add pagination for message history
- add citations/source chunk references in assistant payloads
- support conversation-level system prompts and retrieval tuning
