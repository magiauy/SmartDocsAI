import math

import pytest


def test_embedding_service_uses_gemini_batch_embeddings(mocker):
    from apps.retrieval.services.embedding_service import EmbeddingService

    response = mocker.Mock()
    response.headers = {"content-type": "application/json"}
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "embeddings": [
            {"values": [1.0, 0.0, 0.0, 0.0]},
            {"values": [0.0, 2.0, 0.0, 0.0]},
        ]
    }

    client = mocker.Mock()
    client.post.return_value = response

    client_cm = mocker.Mock()
    client_cm.__enter__ = mocker.Mock(return_value=client)
    client_cm.__exit__ = mocker.Mock(return_value=False)

    mocker.patch("apps.retrieval.services.embedding_service.httpx.Client", return_value=client_cm)

    service = EmbeddingService(provider="gemini", gemini_api_key="test-key", vector_size=4, strict=True)
    vectors = service.embed_texts(["first", "second"])

    assert len(vectors) == 2
    assert len(vectors[0]) == 4
    assert math.isclose(sum(value * value for value in vectors[0]), 1.0, rel_tol=1e-6)
    assert math.isclose(sum(value * value for value in vectors[1]), 1.0, rel_tol=1e-6)


@pytest.mark.parametrize("method_name,input_value", [("embed_query", "What is RAG?"), ("embed_texts", ["Chunk text"])] )
def test_embedding_service_falls_back_when_gemini_is_unavailable(method_name, input_value):
    from apps.retrieval.services.embedding_service import EmbeddingService

    service = EmbeddingService(provider="gemini", gemini_api_key="", vector_size=8, strict=False)
    result = getattr(service, method_name)(input_value)

    if method_name == "embed_query":
        assert len(result) == 8
    else:
        assert len(result) == 1
        assert len(result[0]) == 8


def test_embedding_service_raises_when_strict_and_gemini_key_missing():
    from apps.retrieval.services.embedding_service import EmbeddingService

    service = EmbeddingService(provider="gemini", gemini_api_key="", vector_size=8, strict=True)

    with pytest.raises(RuntimeError):
        service.embed_texts(["must fail"])