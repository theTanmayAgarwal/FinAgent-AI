from finagent.core.config import get_settings


class ResearchMemory:
    def __init__(self):
        self.client = None
        try:
            import chromadb

            self.client = chromadb.PersistentClient(path=str(get_settings().chroma_path))
            self.collection = self.client.get_or_create_collection("research_evidence")
        except Exception:
            self.collection = None

    def add(self, report_id: str, ticker: str, thesis: str) -> None:
        if self.collection:
            self.collection.upsert(
                ids=[report_id], documents=[thesis], metadatas=[{"ticker": ticker}]
            )

    def search(self, query: str, limit: int = 5) -> list[dict]:
        if not self.collection:
            return []
        result = self.collection.query(query_texts=[query], n_results=limit)
        return [
            {"id": i, "text": d, "metadata": m}
            for i, d, m in zip(result["ids"][0], result["documents"][0], result["metadatas"][0])
        ]
