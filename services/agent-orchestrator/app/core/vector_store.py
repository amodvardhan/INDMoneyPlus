"""Vector store integration for agent memory"""
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector store for agent memory and context retrieval"""
    
    def __init__(self):
        self.store_type = settings.vector_db_type
        self._store = None
    
    async def initialize(self):
        """Initialize vector store connection"""
        if self.store_type == "pinecone" and settings.pinecone_api_key:
            try:
                from pinecone import Pinecone
                pc = Pinecone(api_key=settings.pinecone_api_key)
                self._store = pc.Index(settings.pinecone_index_name)
                logger.info("Pinecone vector store initialized")
            except ImportError:
                logger.warning("Pinecone client not installed. Using in-memory store.")
                self._store = {}
            except Exception as e:
                logger.warning(f"Failed to initialize Pinecone: {e}. Using in-memory store.")
                self._store = {}
        else:
            # In-memory store for development/testing
            self._store = {}
            logger.info("Using in-memory vector store")
    
    async def store(self, text: str, metadata: Dict[str, Any], embedding: Optional[List[float]] = None):
        """Store text with metadata in vector store"""
        if isinstance(self._store, dict):
            # In-memory storage
            import hashlib
            key = hashlib.md5(text.encode()).hexdigest()
            self._store[key] = {
                "text": text,
                "metadata": metadata,
                "embedding": embedding
            }
        else:
            # Pinecone storage
            if embedding:
                self._store.upsert([(key, embedding, metadata)])
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search vector store for similar content"""
        if isinstance(self._store, dict):
            # In-memory: return all entries (simple implementation)
            results = []
            for key, value in list(self._store.items())[:top_k]:
                results.append({
                    "text": value["text"],
                    "metadata": value["metadata"],
                    "score": 0.8  # Mock score
                })
            return results
        else:
            # Pinecone search
            try:
                # Generate embedding for query (would use OpenAI embeddings in production)
                results = self._store.query(
                    vector=[0.0] * 1536,  # Placeholder - would be actual embedding
                    top_k=top_k,
                    include_metadata=True
                )
                return [
                    {
                        "text": match.metadata.get("text", ""),
                        "metadata": match.metadata,
                        "score": match.score
                    }
                    for match in results.matches
                ]
            except Exception as e:
                logger.error(f"Vector search error: {e}")
                return []


# Global vector store instance
_vector_store: Optional[VectorStore] = None


async def get_vector_store() -> VectorStore:
    """Get or initialize vector store"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
        await _vector_store.initialize()
    return _vector_store

