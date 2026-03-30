import httpx

from apps.llm.interfaces.base import CompletionRequest, CompletionResponse


class GeminiClient:
    provider_name = "gemini"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{request.model or self.model}:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": request.prompt}]}]}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        content = ""
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            content = "".join(part.get("text", "") for part in parts)
        return CompletionResponse(provider=self.provider_name, model=request.model or self.model, content=content)
