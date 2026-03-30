from apps.llm.interfaces.base import CompletionRequest, CompletionResponse


class MockClient:
    provider_name = "mock"

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(
            provider=self.provider_name,
            model=request.model or "mock-1",
            content=f"Mock response for: {request.prompt}",
            tokens_input=10,
            tokens_output=20,
            latency_ms=1,
        )
