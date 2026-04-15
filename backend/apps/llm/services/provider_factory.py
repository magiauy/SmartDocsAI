from apps.llm.clients.gemini import GeminiClient
from apps.llm.clients.mock import MockClient
from apps.llm.clients.ollama import OllamaClient


class ProviderFactory:
    def __init__(self, settings_obj):
        self.settings = settings_obj

    def build(self, provider: str):
        if provider == "gemini" and getattr(self.settings, "GEMINI_API_KEY", ""):
            return GeminiClient(getattr(self.settings, "GEMINI_API_KEY", ""), getattr(self.settings, "GEMINI_MODEL", "gemini-2.5-flash"))
        if provider == "ollama" and getattr(self.settings, "OLLAMA_BASE_URL", ""):
            return OllamaClient(getattr(self.settings, "OLLAMA_BASE_URL", ""), getattr(self.settings, "OLLAMA_MODEL", "qwen2:1.5b"))
        return MockClient()

    def describe(self):
        return [
            {"name": "gemini", "configured": bool(getattr(self.settings, "GEMINI_API_KEY", ""))},
            {"name": "ollama", "configured": bool(getattr(self.settings, "OLLAMA_BASE_URL", ""))},
            {"name": "mock", "configured": True},
        ]
