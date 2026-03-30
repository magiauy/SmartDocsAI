from asgiref.sync import async_to_sync
from django.conf import settings

from apps.llm.interfaces.base import CompletionRequest
from apps.llm.services.provider_factory import ProviderFactory


class CompletionService:
    def __init__(self, factory=None):
        self.factory = factory or ProviderFactory(settings)

    def generate(self, provider: str, model: str, prompt: str, context_hits: list[dict] | None = None):
        request = CompletionRequest(provider=provider, model=model, prompt=prompt, context_hits=context_hits or [])
        client = self.factory.build(provider)
        response = async_to_sync(client.generate)(request)
        return {
            "provider": response.provider,
            "model": response.model,
            "content": response.content,
            "tokens_input": response.tokens_input,
            "tokens_output": response.tokens_output,
            "latency_ms": response.latency_ms,
        }
