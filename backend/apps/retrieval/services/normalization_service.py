import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class NormalizedDocument:
    document_id: int
    normalized_text: str
    metadata: dict
    content_hash: str


class NormalizationService:
    async def normalize_text(self, text: str, metadata: dict):
        collapsed = re.sub(r"[ \t]+", " ", text)
        collapsed = re.sub(r"\n{3,}", "\n\n", collapsed)
        collapsed = "\n\n".join(part.strip() for part in collapsed.strip().split("\n\n") if part.strip())
        return NormalizedDocument(
            document_id=metadata.get("document_id", 0),
            normalized_text=collapsed,
            metadata=metadata,
            content_hash=str(hash(collapsed)),
        )

    async def normalize_document(self, document):
        file_path = Path(document.file_path)
        text = file_path.read_text(encoding="utf-8") if file_path.exists() else document.title
        return await self.normalize_text(text, {"document_id": document.id, "title": document.title})
