# src/vector_db/qdrant_client.py
from typing import List, Dict, Any, Optional
import logging
import random

logger = logging.getLogger(__name__)

class QdrantClient:
    """Qdrant client stub (in-memory mode)"""
    
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.host = host
        self.port = port
        self.collections = {}
        logger.info(f"Qdrant client initialized (in-memory) at {host}:{port}")
    
    def search(self, embedding: List[float], top_k: int = 5, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        # Return mock results
        mock_documents = [
            {
                "id": "doc1",
                "score": 0.95,
                "text": "Actiboost offers comprehensive construction services including site preparation, foundation work, structural framing, electrical and plumbing installation, and interior finishing.",
                "metadata": {"source": "construction_contract.txt"}
            },
            {
                "id": "doc2",
                "score": 0.85,
                "text": "Project Estimate: Commercial Building Construction in Mumbai. Total estimated cost: Rs. 1,04,00,000.",
                "metadata": {"source": "project_estimate.txt"}
            },
            {
                "id": "doc3",
                "score": 0.75,
                "text": "Material Specifications: Cement (PPC - 43 Grade), Steel (TMT Fe 500), Concrete (M20 Grade)",
                "metadata": {"source": "material_specifications.txt"}
            },
            {
                "id": "doc4",
                "score": 0.65,
                "text": "Safety Policy: OSHA compliance, PPE requirements, fall protection, electrical safety, fire safety, emergency response.",
                "metadata": {"source": "safety_policy.txt"}
            }
        ]
        
        return mock_documents[:top_k]