import os
import json
import logging
import faiss
import numpy as np

logger = logging.getLogger(__name__)

class VectorStore:
    """Manages raw FAISS index and local JSON metadata storage."""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Cosine similarity on normalized vectors
        self.metadata = []  # List of chunks

    def add_chunks(self, chunks: list[dict], embeddings: list[list[float]]) -> None:
        """Adds text chunks and their embeddings to the store."""
        if not chunks or not embeddings:
            return
            
        assert len(chunks) == len(embeddings), "Chunks and embeddings size mismatch"
        
        # Convert embeddings to float32 numpy array and normalize
        vectors = np.array(embeddings).astype("float32")
        faiss.normalize_L2(vectors)
        
        # Add to index
        self.index.add(vectors)
        
        # Add to metadata
        self.metadata.extend(chunks)
        logger.info(f"Added {len(chunks)} chunks to VectorStore. Total chunks: {len(self.metadata)}")

    def save(self, path_prefix: str) -> None:
        """Saves the FAISS index and metadata JSON to disk."""
        # Ensure directories exist
        os.makedirs(os.path.dirname(path_prefix), exist_ok=True)
        
        # Save FAISS index
        index_path = f"{path_prefix}.index"
        faiss.write_index(self.index, index_path)
        
        # Save metadata
        metadata_path = f"{path_prefix}_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Vector store saved successfully at {path_prefix}")

    def load(self, path_prefix: str) -> bool:
        """Loads FAISS index and metadata from disk. Returns True if successful."""
        index_path = f"{path_prefix}.index"
        metadata_path = f"{path_prefix}_metadata.json"
        
        if not os.path.exists(index_path) or not os.path.exists(metadata_path):
            logger.warning(f"Index files not found at {path_prefix}")
            return False
            
        try:
            self.index = faiss.read_index(index_path)
            with open(metadata_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            self.dimension = self.index.d
            logger.info(f"Vector store loaded successfully from {path_prefix}. Total chunks: {len(self.metadata)}")
            return True
        except Exception as e:
            logger.error(f"Failed to load vector store from {path_prefix}: {e}")
            return False

    def search(self, query_embedding: list[float], k: int = 5) -> list[tuple[dict, float]]:
        """
        Searches the index with query embedding.
        Returns list of (chunk_metadata, cosine_similarity_score).
        """
        if self.index.ntotal == 0:
            return []
            
        # Format query vector
        query_vector = np.array([query_embedding]).astype("float32")
        faiss.normalize_L2(query_vector)
        
        # Perform search
        k = min(k, self.index.ntotal)
        scores, indices = self.index.search(query_vector, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append((self.metadata[idx], float(score)))
            
        return results

    def clear(self) -> None:
        """Clears all stored indices and metadata."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []
        logger.info("VectorStore cleared.")
