import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generates embeddings using sentence-transformers."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        logger.info(f"Loading sentence-transformers model '{model_name}'...")
        self.model = SentenceTransformer(model_name)
        logger.info("Sentence-transformers model loaded successfully.")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generates list of float list embeddings for the input texts."""
        if not texts:
            return []
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
