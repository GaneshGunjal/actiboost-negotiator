import json
from pathlib import Path
from typing import Any, Dict, List


class SimpleIndexer:
    """A lightweight indexer that stores text chunks for retrieval."""

    def __init__(self, index_dir: str = "logs/index"):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_dir / "documents.json"
        self.documents: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if self.index_path.exists():
            try:
                self.documents = json.loads(self.index_path.read_text(encoding="utf-8"))
            except Exception:
                self.documents = []

    def _save(self):
        self.index_path.write_text(json.dumps(self.documents, indent=2), encoding="utf-8")

    def add_document(self, document_id: str, text: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
        entry = {
            "id": document_id,
            "text": text,
            "metadata": metadata or {},
        }
        self.documents.append(entry)
        self._save()
        return entry

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        for doc in documents:
            self.add_document(doc.get("id", f"doc-{len(self.documents)}"), doc.get("text", ""), doc.get("metadata", {}))

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_lower = (query or "").lower()
        scored = []
        for doc in self.documents:
            text = (doc.get("text") or "").lower()
            score = sum(1 for term in query_lower.split() if term and term in text)
            if score > 0:
                scored.append({"id": doc["id"], "score": score, "text": doc["text"], "metadata": doc.get("metadata", {})})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
