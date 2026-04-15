import asyncio
from types import SimpleNamespace


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


def test_normalization_falls_back_to_ocr_for_pdf(tmp_path):
    from apps.retrieval.services.normalization_service import NormalizationService

    class DummyOCRService:
        async def extract_text_from_pdf(self, file_path):
            return "OCR extracted text"

    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"not-a-real-pdf")

    document = SimpleNamespace(id=123, title="Fallback", file_path=str(pdf_path))
    service = NormalizationService(ocr_service=DummyOCRService())
    normalized = asyncio.run(service.normalize_document(document))

    assert normalized.normalized_text == "OCR extracted text"
    assert normalized.document_id == 123
