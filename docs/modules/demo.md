# Demo Module

## Purpose

`demo` serves a browser page from Django so the current backend can be exercised without a separate frontend stack.

It is intentionally thin and should stay a consumer of existing APIs, not a second business layer.

## Main Files

- `backend/apps/demo/views.py`
  - serves the page and ensures CSRF cookie is present
- `backend/apps/demo/urls.py`
  - route for `/demo/`
- `backend/apps/demo/templates/demo/index.html`
  - demo page layout
- `backend/apps/demo/static/demo/demo.css`
  - demo styling
- `backend/apps/demo/static/demo/demo.js`
  - browser logic for upload, document selection, conversation creation, polling, and chat

## Current Demo Flow

1. upload one or many files
2. refresh or inspect documents list
3. select documents
4. create a conversation
5. poll conversation status until `ready`
6. load bootstrap summary messages
7. send questions in the chat form

## API Usage

The page calls:

- `POST /api/documents/upload/`
- `GET /api/documents/`
- `POST /api/conversations/`
- `GET /api/conversations/{id}/status/`
- `GET /api/conversations/{id}/messages/`
- `POST /api/conversations/{id}/messages/`

## Dependencies

- depends on same-origin requests to the Django backend
- relies on CSRF cookie from the demo view
- does not depend on a frontend framework

## What To Extend Next

- show retrieval hits or citations in the UI
- render document summary cards once processing finishes
- add better loading and failure states for long-running background work
