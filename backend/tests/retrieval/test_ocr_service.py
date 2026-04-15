def test_ocr_service_builds_bearer_auth_header():
    from apps.retrieval.services.ocr_service import OCRService

    service = OCRService(
        api_url="https://example.com/ocr",
        api_key="secret-token",
        api_key_header="Authorization",
        api_key_prefix="Bearer",
    )

    headers = service._build_headers()
    assert headers["Authorization"] == "Bearer secret-token"


def test_ocr_service_collects_nested_text_lines():
    from apps.retrieval.services.ocr_service import OCRService

    service = OCRService(api_url="https://example.com/ocr")
    payload = {
        "result": [
            [[0, 0], [10, 0], [10, 10], [0, 10]],
            ["Hello", 0.99],
        ],
        "data": {
            "rec_texts": ["World", "From OCR"],
        },
    }

    lines = service._collect_text_lines(payload)
    assert "Hello" in lines
    assert "World" in lines
    assert "From OCR" in lines


def test_ocr_service_rejects_invalid_extra_params_json():
    from apps.retrieval.services.ocr_service import OCRService

    try:
        OCRService(api_url="https://example.com/ocr", extra_params_json="[]")
        assert False, "Expected ValueError for non-object JSON"
    except ValueError as exc:
        assert "JSON object" in str(exc)


def test_ocr_service_extracts_aistudio_markdown_lines():
    from apps.retrieval.services.ocr_service import OCRService

    service = OCRService(api_url="https://example.com/ocr", request_mode="aistudio-job")
    payload = {
        "result": {
            "layoutParsingResults": [
                {"markdown": {"text": "Page 1 content"}},
                {"markdown": {"text": "Page 2 content"}},
            ]
        }
    }

    lines = service._extract_aistudio_markdown_lines(payload)
    assert lines == ["Page 1 content", "Page 2 content"]


def test_ocr_service_aistudio_falls_back_to_generic_collection_when_missing_markdown():
    from apps.retrieval.services.ocr_service import OCRService

    service = OCRService(api_url="https://example.com/ocr", request_mode="aistudio-job")
    payload = {
        "result": {
            "layoutParsingResults": [],
        },
        "data": {
            "rec_texts": ["Fallback A", "Fallback B"],
        },
    }

    lines = service._extract_aistudio_markdown_lines(payload)
    assert "Fallback A" in lines
    assert "Fallback B" in lines