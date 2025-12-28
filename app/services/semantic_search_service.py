"""Semantic search service using Supabase pgvector.

Workflow:
1. User query → Embed query (multilingual-e5-large)
2. Call Supabase RPC match_documents(query_vector)
3. pgvector returns top K chunks by cosine similarity
4. Return results with metadata (source, title, commodity, etc.)

Performance: <100ms per query (HNSW index)
Cost: $0 (Supabase free tier)
"""
from typing import List, Dict, Any, Optional
import logging

from app.services.supabase_service import SupabaseService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """
    Semantic search using Supabase pgvector.

    Features:
    - Multilingual search (Khmer, English, Vietnamese)
    - Fast similarity search (<100ms with HNSW index)
    - Metadata filtering (by commodity, source, etc.)
    - Top-K retrieval (configurable)
    """

    def __init__(
        self,
        supabase: SupabaseService,
        embedding: EmbeddingService
    ):
        """
        Initialize semantic search service.

        Args:
            supabase: SupabaseService instance (for database access)
            embedding: EmbeddingService instance (for query embedding)
        """
        self.supabase = supabase
        self.embedding = embedding

        logger.info("SemanticSearchService initialized")

    async def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        commodity: Optional[str] = None,
        source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search in document embeddings.

        Args:
            query: Search query (any language: Khmer, English, Vietnamese)
            top_k: Number of results to return (default: 5)
            similarity_threshold: Minimum cosine similarity (0.0-1.0, default: 0.7)
                                 - 0.7+ = High relevance
                                 - 0.6-0.7 = Medium relevance
                                 - <0.6 = Low relevance (usually filtered out)
            commodity: Filter by commodity (optional: 'cashew', 'rubber')
            source: Filter by source (optional: 'GDrive', 'ODC', etc.)

        Returns:
            List of search results, each with structure:
            {
                'id': UUID,
                'document_id': UUID,
                'chunk_index': int,
                'chunk_text': str,
                'similarity': float (0.0-1.0),
                'metadata': {
                    'source': str,
                    'commodity': str,
                    'title': str,
                    'url': str,
                    ...
                }
            }

        Example:
            >>> search = SemanticSearchService(supabase, embedding)
            >>> results = await search.search(
            ...     "ការផលិតស្វាយចន្ទី",  # Khmer: cashew production
            ...     top_k=3,
            ...     commodity="cashew"
            ... )
            >>> len(results)
            3
            >>> results[0]['similarity']
            0.8538
            >>> results[0]['metadata']['source']
            'GDrive'

        Performance:
            - Query embedding: ~50-100ms (CPU)
            - pgvector search: <50ms (HNSW index)
            - Total: <150ms

        Note:
            Uses cosine similarity (<=> operator in pgvector)
            Automatically uses "query: " prefix for E5 model.
        """
        # Step 1: Embed query
        logger.info(f"Semantic search query: '{query[:50]}...'")

        try:
            query_vector = self.embedding.embed_query(query)
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise

        # Step 2: Call Supabase RPC match_documents
        try:
            result = self.supabase.client.rpc(
                "match_documents",
                {
                    "query_embedding": query_vector,
                    "match_count": top_k,
                    "match_threshold": similarity_threshold,
                    "filter_commodity": commodity  # NULL if not specified
                }
            ).execute()

            matches = result.data if result.data else []

        except Exception as e:
            logger.error(f"Error in pgvector search: {e}")
            raise

        # Step 3: Post-filter by source if specified
        if source:
            matches = [
                m for m in matches
                if m.get('metadata', {}).get('source') == source
            ]

        logger.info(
            f"Search returned {len(matches)} results "
            f"(threshold: {similarity_threshold}, top_k: {top_k})"
        )

        return matches

    async def search_with_context(
        self,
        query: str,
        top_k: int = 5,
        commodity: Optional[str] = None
    ) -> str:
        """
        Get formatted context string for RAG.

        This is a convenience method that:
        1. Performs semantic search
        2. Formats top K chunks as context string
        3. Returns ready-to-use context for Perplexity RAG

        Args:
            query: Search query
            top_k: Number of chunks to retrieve (default: 5)
            commodity: Filter by commodity (optional)

        Returns:
            Formatted context string:
            ```
            [Source 1: GDrive - iTrade Bulletin]
            Cashew production in Cambodia has increased...

            ---

            [Source 2: ODC - Agricultural Report]
            Kampong Thom province produces 5,200 tons...

            ---
            ...
            ```

        Example:
            >>> search = SemanticSearchService(supabase, embedding)
            >>> context = await search.search_with_context(
            ...     "Cashew export statistics",
            ...     top_k=3,
            ...     commodity="cashew"
            ... )
            >>> print(len(context))
            5432  # ~5KB context for Perplexity
            >>> # Use context in Perplexity RAG query
            >>> response = await perplexity.rag_query(query, context, "cashew")

        Performance:
            Same as search() + minimal string formatting overhead
        """
        results = await self.search(query, top_k=top_k, commodity=commodity)

        if not results:
            logger.warning(f"No results found for query: '{query[:50]}...'")
            return "No relevant context found in documents."

        context_parts = []

        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            source = metadata.get('source', 'Unknown')
            title = metadata.get('title', 'Untitled')
            similarity = result.get('similarity', 0.0)
            text = result.get('chunk_text', '')

            # Format: [Source N: SOURCE - TITLE] (Similarity: X.XX)
            header = f"[Source {i}: {source} - {title[:50]}] (Similarity: {similarity:.2f})"
            context_parts.append(f"{header}\n{text}")

        # Join with separator
        context = "\n\n---\n\n".join(context_parts)

        logger.info(
            f"Context generated: {len(context)} chars from {len(results)} chunks"
        )

        return context

    async def get_similar_chunks(
        self,
        chunk_text: str,
        top_k: int = 3,
        exclude_document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar chunks to a given chunk (for related content discovery).

        Use this for:
        - "Related documents" feature
        - Duplicate detection
        - Cross-referencing

        Args:
            chunk_text: Text of chunk to find similar to
            top_k: Number of similar chunks
            exclude_document_id: Exclude chunks from this document (optional)

        Returns:
            List of similar chunks (same structure as search())

        Example:
            >>> chunk = "Cashew production statistics for Kampong Thom"
            >>> similar = await search.get_similar_chunks(chunk, top_k=3)
            >>> for s in similar:
            ...     print(f"{s['similarity']:.2f} - {s['metadata']['title']}")
            0.89 - ODC Agricultural Report 2023
            0.84 - iTrade Bulletin Q2 2024
            0.79 - Economic Land Concessions Study
        """
        # Embed the chunk text (use passage prefix)
        try:
            chunk_vector = self.embedding.embed_text(chunk_text)
        except Exception as e:
            logger.error(f"Error embedding chunk: {e}")
            raise

        # Search using chunk vector
        try:
            result = self.supabase.client.rpc(
                "match_documents",
                {
                    "query_embedding": chunk_vector,
                    "match_count": top_k + 10,  # Get extra in case we need to filter
                    "match_threshold": 0.6  # Lower threshold for related content
                }
            ).execute()

            matches = result.data if result.data else []

        except Exception as e:
            logger.error(f"Error finding similar chunks: {e}")
            raise

        # Filter out chunks from same document if requested
        if exclude_document_id:
            matches = [
                m for m in matches
                if m.get('document_id') != exclude_document_id
            ]

        # Return top K
        return matches[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get semantic search statistics.

        Returns:
            Dict with service stats

        Example:
            >>> stats = search.get_stats()
            >>> print(stats)
            {
                'embedding_model': 'intfloat/multilingual-e5-large',
                'embedding_dimension': 1024,
                'vector_db': 'Supabase pgvector',
                'index_type': 'HNSW',
                'supported_languages': ['Khmer', 'English', 'Vietnamese', '100+'],
                'default_threshold': 0.7,
                'default_top_k': 5
            }
        """
        model_info = self.embedding.get_model_info()

        return {
            'embedding_model': model_info['model_name'],
            'embedding_dimension': model_info['dimension'],
            'vector_db': 'Supabase pgvector',
            'index_type': 'HNSW (m=16, ef_construction=64)',
            'supported_languages': ['Khmer', 'English', 'Vietnamese', '100+ total'],
            'default_threshold': 0.7,
            'default_top_k': 5,
            'cost': '$0 (Supabase free tier + local embeddings)',
            'performance': '<100ms per query (with HNSW index)'
        }


# Module-level convenience function
async def quick_search(
    query: str,
    supabase_url: str,
    supabase_key: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Quick semantic search without service initialization.

    Use this for:
    - CLI scripts
    - Quick testing
    - One-off searches

    Args:
        query: Search query
        supabase_url: Supabase project URL
        supabase_key: Supabase API key
        top_k: Number of results

    Returns:
        List of search results

    Example:
        >>> from app.services.semantic_search_service import quick_search
        >>> from app.config import settings
        >>> results = await quick_search(
        ...     "cashew",
        ...     settings.supabase_url,
        ...     settings.supabase_key
        ... )

    Warning:
        Creates new service instances (slower than reusing).
        For production, use SemanticSearchService directly.
    """
    supabase = SupabaseService(supabase_url, supabase_key)
    embedding = EmbeddingService()
    search = SemanticSearchService(supabase, embedding)

    return await search.search(query, top_k=top_k)
