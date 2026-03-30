from langchain_text_splitters import RecursiveCharacterTextSplitter


class ChunkingService:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def chunk(self, normalized_document):
        texts = self.splitter.split_text(normalized_document.normalized_text or "")
        return [
            {
                "content": text,
                "metadata": {**normalized_document.metadata, "chunk_index": index},
            }
            for index, text in enumerate(texts)
        ]
