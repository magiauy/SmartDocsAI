class SummarizationService:
    def summarize(self, document, chunks):
        if chunks:
            return {"summary": chunks[0]["content"][:200]}
        return {"summary": f"Summary for {document.title}"}
