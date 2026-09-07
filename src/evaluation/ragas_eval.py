from typing import Any, Dict, List

RAGAS_METRIC_MATRIX: List[Dict[str, str]] = [
    {"metric": "faithfulness", "purpose": "Check whether the answer is supported by the retrieved context."},
    {"metric": "answer_relevancy", "purpose": "Measure how directly the answer addresses the user request."},
    {"metric": "context_precision", "purpose": "Verify the retrieved context contains the most relevant snippets first."},
    {"metric": "context_recall", "purpose": "Ensure the context covers the essential facts needed for the answer."},
    {"metric": "harmfulness", "purpose": "Flag unsafe, manipulative, or non-compliant output."},
    {"metric": "conversation_quality", "purpose": "Score continuity, coherence, and context retention in negotiation dialogues."},
]


def build_evaluation_matrix() -> List[Dict[str, str]]:
    """Return the current Ragas-style matrix used for negotiation evaluation."""
    return [dict(metric) for metric in RAGAS_METRIC_MATRIX]


def evaluate_negotiation_run(question: str, answer: str, contexts: List[str]) -> Dict[str, Any]:
    """Return a lightweight evaluation payload when the full Ragas library is unavailable."""
    context_text = "\n".join(contexts or [])
    payload = {
        "question": question,
        "answer": answer,
        "contexts": contexts,
        "metrics": build_evaluation_matrix(),
        "summary": {
            "faithfulness": 1.0 if context_text and answer and question else 0.0,
            "answer_relevancy": 1.0 if answer and question else 0.0,
            "context_precision": 1.0 if contexts else 0.0,
            "context_recall": 1.0 if contexts else 0.0,
            "harmfulness": 0.0,
            "conversation_quality": 1.0 if answer and question else 0.0,
        },
    }
    return payload
