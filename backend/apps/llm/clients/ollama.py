import time

import httpx

from apps.llm.interfaces.base import CompletionRequest, CompletionResponse


class OllamaClient:
    provider_name = "ollama"

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        started_at = time.perf_counter()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": request.model or self.model,
                    "prompt": request.prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_ctx": 8192,
                        "num_predict": 256,
                    },
                },
            )
            response.raise_for_status()
            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        return CompletionResponse(
            provider=self.provider_name,
            model=request.model or self.model,
            content=data.get("response", ""),
            latency_ms=elapsed_ms,
        )
