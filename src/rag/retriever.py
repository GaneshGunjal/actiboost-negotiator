# src/rag/retriever.py
from typing import List, Dict, Any
from src.vector_db.qdrant_client import QdrantClient
from src.utils.groq_client import groq
from src.utils.logfire_config import logfire_trace
import logging

logger = logging.getLogger(__name__)

class RAGRetriever:
    """
    Retrieves relevant documents from Qdrant using semantic search.
    """
    
    def __init__(self, qdrant_client: QdrantClient):
        self.qdrant_client = qdrant_client
    
    @logfire_trace(name="RAG - Search")
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        try:
            # Generate embedding for query
            embedding = await self._get_embedding(query)
            
            # Search Qdrant
            results = self.qdrant_client.search(
                embedding=embedding,
                top_k=top_k,
                threshold=0.5
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        # Using a simple approach - you can integrate with a proper embedding model
        # For now, we'll use a simulation with GROQ
        try:
            response = await groq.ask_json(
                f"Generate a numerical vector representation for this text. Return only a list of 128 numbers.\n\nText: {text}"
            )
            
            if "error" not in response:
                return response.get("embedding", [0.0] * 128)
            
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
        
        # Fallback: random embedding
        import random
        return [random.random() for _ in range(128)]