from __future__ import annotations

import hashlib
import math
from threading import Lock

import httpx
from django.conf import settings


class EmbeddingService:
    _model_cache = {}
    _cache_lock = Lock()

    def __init__(
        self,
        provider: str | None = None,
        model_name: str | None = None,
        vector_size: int | None = None,
        strict: bool | None = None,
        device: str | None = None,
        gemini_api_key: str | None = None,
        timeout_seconds: int | None = None,
    ):
        self.provider = (provider or getattr(settings, "EMBEDDING_PROVIDER", "gemini")).strip().lower()
        self.model_name = model_name or getattr(settings, "EMBEDDING_MODEL_NAME", "gemini-embedding-2-preview")
        self.vector_size = int(vector_size or getattr(settings, "EMBEDDING_VECTOR_SIZE", 1024))
        self.strict = bool(getattr(settings, "EMBEDDING_STRICT", False) if strict is None else strict)
        self.device = device or getattr(settings, "EMBEDDING_DEVICE", "cpu")
        self.timeout_seconds = int(timeout_seconds or getattr(settings, "EMBEDDING_TIMEOUT_SECONDS", 30))
        if gemini_api_key is None:
            self.gemini_api_key = getattr(settings, "GEMINI_API_KEY", "").strip()
        else:
            self.gemini_api_key = gemini_api_key.strip()
        self.gemini_task_type_document = getattr(settings, "EMBEDDING_GEMINI_TASK_TYPE_DOCUMENT", "RETRIEVAL_DOCUMENT")
        self.gemini_task_type_query = getattr(settings, "EMBEDDING_GEMINI_TASK_TYPE_QUERY", "RETRIEVAL_QUERY")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            if self.provider == "gemini":
                vectors = self._embed_with_gemini(texts, task_type=self.gemini_task_type_document)
                return [self._normalize(vector) for vector in vectors]

            model = self._get_model()
            vectors = model.encode(texts, normalize_embeddings=True)
            return [vector.tolist() for vector in vectors]
        except Exception:
            if self.strict:
                raise
            return [self._fallback_embedding(text) for text in texts]

    def embed_query(self, query: str) -> list[float]:
        if self.provider == "gemini":
            try:
                vectors = self._embed_with_gemini([query], task_type=self.gemini_task_type_query)
                return self._normalize(vectors[0]) if vectors else []
            except Exception:
                if self.strict:
                    raise
                return self._fallback_embedding(query)

        vectors = self.embed_texts([query])
        return vectors[0] if vectors else []

    def _get_model(self):
        if self.provider == "gemini":
            raise RuntimeError("Gemini provider does not use a local sentence-transformers model")

        with self._cache_lock:
            if self.model_name in self._model_cache:
                return self._model_cache[self.model_name]

            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self.model_name, device=self.device)
            self._model_cache[self.model_name] = model
            return model

    def _embed_with_gemini(self, texts: list[str], task_type: str) -> list[list[float]]:
        if not self.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required for Gemini embeddings")

        try:
            return self._gemini_batch_embed(texts=texts, task_type=task_type, with_dimension=True)
        except httpx.HTTPStatusError:
            # Some API versions may reject outputDimensionality or batch embedding shape.
            try:
                return self._gemini_batch_embed(texts=texts, task_type=task_type, with_dimension=False)
            except Exception:
                return [self._gemini_single_embed(text=text, task_type=task_type, with_dimension=False) for text in texts]

    def _gemini_batch_embed(self, texts: list[str], task_type: str, with_dimension: bool) -> list[list[float]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:batchEmbedContents?key={self.gemini_api_key}"
        requests_payload = [self._gemini_embed_request(text=text, task_type=task_type, with_dimension=with_dimension) for text in texts]
        payload = {"requests": requests_payload}

        with httpx.Client(timeout=float(self.timeout_seconds)) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}

        embeddings = data.get("embeddings", [])
        values = [item.get("values", []) for item in embeddings if isinstance(item, dict)]
        if len(values) != len(texts) or any(not vector for vector in values):
            raise RuntimeError("Unexpected Gemini batch embedding response")
        return values

    def _gemini_single_embed(self, text: str, task_type: str, with_dimension: bool) -> list[float]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:embedContent?key={self.gemini_api_key}"
        payload = self._gemini_embed_request(text=text, task_type=task_type, with_dimension=with_dimension)

        with httpx.Client(timeout=float(self.timeout_seconds)) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}

        values = data.get("embedding", {}).get("values", [])
        if not values:
            raise RuntimeError("Unexpected Gemini embedding response")
        return values

    def _gemini_embed_request(self, text: str, task_type: str, with_dimension: bool) -> dict:
        request = {
            "content": {
                "parts": [{"text": text}],
            },
            "taskType": task_type,
        }
        if with_dimension:
            request["outputDimensionality"] = self.vector_size
        return request

    def _normalize(self, vector: list[float]) -> list[float]:
        if not vector:
            return []
        norm = math.sqrt(sum(item * item for item in vector)) or 1.0
        return [item / norm for item in vector]

    def _fallback_embedding(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vector = []
        seed = digest
        while len(vector) < self.vector_size:
            seed = hashlib.sha256(seed).digest()
            for value in seed:
                vector.append((value / 255.0) - 0.5)
                if len(vector) >= self.vector_size:
                    break

        norm = math.sqrt(sum(item * item for item in vector)) or 1.0
        return [item / norm for item in vector]
