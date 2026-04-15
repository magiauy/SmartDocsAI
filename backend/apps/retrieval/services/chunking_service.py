from langchain_text_splitters import RecursiveCharacterTextSplitter
from django.conf import settings


class ChunkingService:
    def __init__(self, chunk_size=None, chunk_overlap=None):
        resolved_chunk_size = int(chunk_size or getattr(settings, "CHUNK_SIZE", 700))
        resolved_chunk_overlap = int(chunk_overlap or getattr(settings, "CHUNK_OVERLAP", 120))
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=resolved_chunk_size, chunk_overlap=resolved_chunk_overlap)

    def chunk(self, normalized_document):
        texts = self.splitter.split_text(normalized_document.normalized_text or "")
        return [
            {
                "content": text,
                "metadata": {**normalized_document.metadata, "chunk_index": index},
            }
            for index, text in enumerate(texts)
        ]
