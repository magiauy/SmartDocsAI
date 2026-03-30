# Core Module

## Purpose

`core` holds shared backend primitives used by the rest of the project:

- health and provider readiness endpoints
- JSON response wrappers
- DRF exception formatting
- light environment access helpers

It is the thin entry layer for cross-cutting concerns, not a business domain.

## Main Files

- `backend/apps/core/api/views.py`
  - `HealthView`, `ProviderListView`, `ProviderTestView`
- `backend/apps/core/api/urls.py`
  - routes mounted under `/api/`
- `backend/apps/core/responses/builders.py`
  - `api_success()` and `api_error()`
- `backend/apps/core/exceptions/handlers.py`
  - DRF exception handler override
- `backend/apps/core/config/env.py`
  - small env helper

## Endpoints

- `GET /api/health/`
- `GET /api/providers/`
- `POST /api/providers/test/`

## Current Behavior

- `health` reports basic service availability flags from current settings
- `providers` reports whether Gemini and Ollama are configured
- `providers/test` resolves a provider and shows whether runtime will use live mode or mock fallback

## Dependencies

- depends on Django settings
- depends on `llm.services.provider_factory.ProviderFactory`
- does not depend on domain models

## What To Extend Next

- add richer health checks for live Redis/Qdrant/MySQL connectivity
- add global request/response tracing IDs
- add API versioning if the surface grows
