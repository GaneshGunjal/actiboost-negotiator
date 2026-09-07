from typing import Any, Dict, List


class FlashReranker:
    """Simple reranker that prefers higher-scoring and more relevant matches."""

    def __init__(self):
        self.weights = {
            "score": 1.0,
            "text_length": 0.01,
        }

    def rerank(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        query_lower = (query or "").lower()
        ranked = []
        for item in results:
            text = item.get("text") or ""
            score = float(item.get("score", 0.0))
            text_length = len(text)
            keyword_hits = sum(1 for term in query_lower.split() if term and term in text.lower())
            adjusted = score + (keyword_hits * 0.2) + (text_length * self.weights["text_length"])
            item = dict(item)
            item["rerank_score"] = adjusted
            ranked.append(item)
        ranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return ranked
