import asyncio


def test_normalization_collapses_extra_whitespace():
    from apps.retrieval.services.normalization_service import NormalizationService

    service = NormalizationService()
    normalized = asyncio.run(
        service.normalize_text(
            "A\n\n\nB   \n\nC",
            {"document_id": 1},
        )
    )

    assert normalized.normalized_text == "A\n\nB\n\nC"
