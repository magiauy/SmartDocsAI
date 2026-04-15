import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from .ocr_service import OCRService


logger = logging.getLogger(__name__)


@dataclass
class NormalizedDocument:
    document_id: int
    normalized_text: str
    metadata: dict
    content_hash: str


class NormalizationService:
    def __init__(self, ocr_service: OCRService | None = None):
        self.ocr_service = ocr_service or OCRService()

    async def normalize_text(self, text: str, metadata: dict):
        collapsed = re.sub(r"[ \t]+", " ", text)
        collapsed = re.sub(r"\n{3,}", "\n\n", collapsed)
        collapsed = "\n\n".join(part.strip() for part in collapsed.strip().split("\n\n") if part.strip())
        return NormalizedDocument(
            document_id=metadata.get("document_id", 0),
            normalized_text=collapsed,
            metadata=metadata,
            content_hash=self._content_hash(collapsed),
        )

    async def normalize_document(self, document):
        file_path = Path(document.file_path)
        text = await self._extract_document_text(document, file_path)
        return await self.normalize_text(text or document.title, {"document_id": document.id, "title": document.title})

    async def _extract_document_text(self, document, file_path: Path) -> str:
        if not file_path.exists():
            return document.title

        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            text = self._extract_pdf_text(file_path)
            if text.strip():
                return text
            return await self.ocr_service.extract_text_from_pdf(file_path)

        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning("Unable to decode file as UTF-8, falling back to OCR: %s", file_path)
            return await self.ocr_service.extract_text_from_pdf(file_path)

    def _extract_pdf_text(self, file_path: Path) -> str:
        try:
            reader = PdfReader(str(file_path))
        except Exception:
            logger.exception("Failed to open PDF for text extraction: %s", file_path)
            return ""

        pages = []
        for page in reader.pages:
            extracted = (page.extract_text() or "").strip()
            if extracted:
                pages.append(extracted)
        return "\n\n".join(pages)

    def _content_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
