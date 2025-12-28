"""Embedding service using multilingual-e5-large (local, free).

Model: intfloat/multilingual-e5-large
Dimension: 1024
Languages: 100+ (including Khmer, English, Vietnamese)
Cost: $0 (local inference via Hugging Face Transformers)

Note: E5 models require "query: " or "passage: " prefix for optimal performance.
"""
from sentence_transformers import SentenceTransformer
from typing import List, Union
import logging
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Multilingual embedding service using Hugging Face Transformers.

    Supports:
    - Khmer (ភាសាខ្មែរ)
    - English
    - Vietnamese (Tiếng Việt)
    - 100+ other languages

    Cost: $0 (local CPU/GPU inference)
    """

    def __init__(self, model_name: str = "intfloat/multilingual-e5-large"):
        """
        Initialize embedding model.

        Args:
            model_name: Hugging Face model identifier
                       Default: intfloat/multilingual-e5-large (1024 dim)

        Note:
            First run will download ~2.2 GB model to cache.
            Subsequent runs use cached model.
        """
        logger.info(f"Loading embedding model: {model_name}")

        try:
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()

            logger.info(f"✅ Model loaded successfully: {self.dimension} dimensions")
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            raise

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text (document passage).

        Use this for:
        - Document chunks (for storage in pgvector)
        - PDF extracts
        - Context passages

        Args:
            text: Text to embed (automatically prefixed with "passage: ")

        Returns:
            List of floats (1024 dimensions for multilingual-e5-large)

        Example:
            >>> service = EmbeddingService()
            >>> vector = service.embed_text("Cashew production in Cambodia")
            >>> len(vector)
            1024
        """
        # E5 models require "passage: " prefix for passages
        prefixed_text = f"passage: {text}"

        try:
            embedding = self.model.encode(prefixed_text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            raise

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        Use this for:
        - User search queries
        - Semantic search input
        - RAG query embedding

        Args:
            query: Query text (automatically prefixed with "query: ")

        Returns:
            List of floats (1024 dimensions)

        Example:
            >>> service = EmbeddingService()
            >>> vector = service.embed_query("ការផលិតស្វាយចន្ទី")  # Khmer: cashew production
            >>> len(vector)
            1024

        Note:
            Uses "query: " prefix (different from passages) for optimal retrieval.
            This is how E5 models achieve best cross-lingual performance.
        """
        # E5 models require "query: " prefix for queries
        prefixed_query = f"query: {query}"

        try:
            embedding = self.model.encode(prefixed_query, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing).

        Use this for:
        - Embedding all document chunks at once
        - Bulk processing during setup
        - Performance optimization (batching is faster than individual calls)

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once (default: 32)
            show_progress: Show progress bar (default: True)

        Returns:
            List of embeddings (each is 1024 dimensions)

        Example:
            >>> service = EmbeddingService()
            >>> texts = ["Text 1", "Text 2", "Text 3"]
            >>> vectors = service.embed_batch(texts)
            >>> len(vectors)
            3
            >>> len(vectors[0])
            1024

        Performance:
            ~50-100 texts/second on CPU
            ~500-1000 texts/second on GPU
        """
        # E5 models: prefix all passages with "passage: "
        prefixed_texts = [f"passage: {text}" for text in texts]

        try:
            embeddings = self.model.encode(
                prefixed_texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error in batch embedding: {e}")
            raise

    def cosine_similarity(
        self,
        embedding1: Union[List[float], np.ndarray],
        embedding2: Union[List[float], np.ndarray]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Use this for:
        - Testing similarity locally
        - Debugging embeddings
        - Validation before pgvector storage

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0.0 to 1.0)
            - 1.0 = identical
            - 0.0 = orthogonal (unrelated)
            - < 0.0 = opposite (rare)

        Example:
            >>> service = EmbeddingService()
            >>> vec1 = service.embed_query("cashew")
            >>> vec2 = service.embed_query("ស្វាយចន្ទី")  # Khmer: cashew
            >>> similarity = service.cosine_similarity(vec1, vec2)
            >>> print(f"Similarity: {similarity:.4f}")
            Similarity: 0.8315  # High similarity (same meaning, different language)

        Note:
            pgvector uses <=> operator (cosine distance = 1 - similarity)
            So: pgvector score 0.2 = similarity 0.8
        """
        # Convert to numpy if needed
        vec1 = np.array(embedding1) if isinstance(embedding1, list) else embedding1
        vec2 = np.array(embedding2) if isinstance(embedding2, list) else embedding2

        # Cosine similarity formula
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def get_model_info(self) -> dict:
        """
        Get model information.

        Returns:
            Dict with model metadata

        Example:
            >>> service = EmbeddingService()
            >>> info = service.get_model_info()
            >>> print(info)
            {
                'model_name': 'intfloat/multilingual-e5-large',
                'dimension': 1024,
                'max_seq_length': 512,
                'languages': '100+',
                'cost': '$0 (local)'
            }
        """
        return {
            'model_name': self.model._model_card_vars.get('model_name', 'multilingual-e5-large'),
            'dimension': self.dimension,
            'max_seq_length': self.model.max_seq_length,
            'languages': '100+ (including Khmer, English, Vietnamese)',
            'cost': '$0 (local inference)',
            'prefix_query': 'query: ',
            'prefix_passage': 'passage: '
        }


# Module-level convenience instance (lazy loading)
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """
    Get singleton embedding service instance.

    Use this to avoid loading model multiple times.

    Example:
        >>> from app.services.embedding_service import get_embedding_service
        >>> service = get_embedding_service()
        >>> vector = service.embed_query("test")

    Returns:
        EmbeddingService instance (singleton)
    """
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService()

    return _embedding_service
