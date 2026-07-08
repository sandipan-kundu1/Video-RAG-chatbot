import logging
from backend.embeddings import EmbeddingGenerator
from backend.vector_store import VectorStore

logger = logging.getLogger(__name__)

class Retriever:
    """Combines VectorStore and EmbeddingGenerator to search for matching chunks."""
    
    def __init__(self, vector_store: VectorStore, embedding_generator: EmbeddingGenerator):
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """Retrieves top K chunks matching the query text."""
        logger.info(f"Retrieving top {top_k} chunks for query: '{query}'")
        
        # Generate embedding for query
        query_embeddings = self.embedding_generator.embed_texts([query])
        if not query_embeddings:
            return []
            
        # Search vector store
        results = self.vector_store.search(query_embeddings[0], k=top_k)
        
        # Extract metadata dictionaries
        chunks = [metadata for metadata, score in results]
        logger.info(f"Retrieved {len(chunks)} chunks successfully.")
        return chunks
