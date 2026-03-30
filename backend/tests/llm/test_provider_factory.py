from types import SimpleNamespace


def test_factory_returns_mock_when_gemini_config_missing():
    from apps.llm.services.provider_factory import ProviderFactory

    settings = SimpleNamespace(
        GEMINI_API_KEY="",
        GEMINI_MODEL="gemini-2.5-flash",
        OLLAMA_BASE_URL="",
        OLLAMA_MODEL="llama3.2",
    )

    client = ProviderFactory(settings).build("gemini")

    assert client.provider_name == "mock"


def test_factory_returns_ollama_when_base_url_exists():
    from apps.llm.services.provider_factory import ProviderFactory

    settings = SimpleNamespace(
        GEMINI_API_KEY="",
        GEMINI_MODEL="gemini-2.5-flash",
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="llama3.2",
    )

    client = ProviderFactory(settings).build("ollama")

    assert client.provider_name == "ollama"
