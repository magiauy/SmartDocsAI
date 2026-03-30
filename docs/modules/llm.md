# LLM Module

## Purpose

`llm` provides a provider-agnostic interface for text generation and a factory that resolves Gemini, Ollama, or mock behavior from settings.

The rest of the codebase should call this module, not provider SDKs directly.

## Main Files

- `backend/apps/llm/interfaces/base.py`
  - `CompletionRequest`
  - `CompletionResponse`
  - `LLMClient` protocol
- `backend/apps/llm/clients/gemini.py`
  - async Gemini adapter
- `backend/apps/llm/clients/ollama.py`
  - async Ollama adapter
- `backend/apps/llm/clients/mock.py`
  - deterministic mock adapter
- `backend/apps/llm/services/provider_factory.py`
  - resolves which client to use
- `backend/apps/llm/services/completion_service.py`
  - sync-friendly wrapper used by the chat module

## Current Behavior

- if Gemini is requested and `GEMINI_API_KEY` exists, use `GeminiClient`
- if Ollama is requested and `OLLAMA_BASE_URL` exists, use `OllamaClient`
- otherwise fall back to `MockClient`

## Request Shape

The internal completion request contains:

- provider
- model
- prompt
- retrieval hits for context

The internal response contains:

- provider
- model
- content
- token counts
- latency

## Dependencies

- depends on `httpx` for outbound calls
- does not depend on Django models
- is consumed by `chat` and observed by `core`

## What To Extend Next

- build proper prompt composition using retrieval hits
- add timeout/retry/error normalization
- store provider raw metadata for debugging
- split embeddings from generation if retrieval moves to a real embedding provider
