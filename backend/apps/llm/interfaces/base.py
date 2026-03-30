from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class CompletionRequest:
    provider: str
    model: str
    prompt: str
    context_hits: list[dict] = field(default_factory=list)


@dataclass
class CompletionResponse:
    provider: str
    model: str
    content: str
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: int = 0


class LLMClient(Protocol):
    provider_name: str

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        ...
