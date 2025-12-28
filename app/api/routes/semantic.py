"""API routes for semantic search and RAG queries."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
import time
import logging

from app.models.rag import (
    SearchRequest, SearchResponse, SearchResult,
    RAGRequest, RAGResponse,
    ConversationHistoryRequest, ConversationHistoryResponse,
    UsageStats, HealthResponse
)
from app.services.supabase_service import SupabaseService
from app.services.embedding_service import EmbeddingService
from app.services.semantic_search_service import SemanticSearchService
from app.services.perplexity_service import PerplexityService
from app.services.cache_service import CacheService
from app.services.budget_service import BudgetService
from app.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["semantic"])

# Initialize services (singleton pattern)
_supabase = None
_embedding = None
_search = None
_perplexity = None
_cache = None
_budget = None


def get_services():
    """Get or initialize services."""
    global _supabase, _embedding, _search, _perplexity, _cache, _budget

    if _supabase is None:
        _supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
    if _embedding is None:
        _embedding = EmbeddingService()
    if _search is None:
        _search = SemanticSearchService(_supabase, _embedding)
    if _perplexity is None:
        _perplexity = PerplexityService(
            api_key=settings.perplexity_api_key,
            max_requests_per_month=1000
        )
    if _cache is None:
        _cache = CacheService(_supabase, ttl_hours=24)
    if _budget is None:
        _budget = BudgetService(_supabase, monthly_budget_usd=5.0)

    return _supabase, _embedding, _search, _perplexity, _cache, _budget


@router.post("/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """
    Semantic search endpoint.

    Performs multilingual vector similarity search over document chunks.

    - **query**: Search query in any language (Khmer, English, Vietnamese)
    - **top_k**: Number of results to return (1-20)
    - **similarity_threshold**: Minimum similarity score (0.0-1.0)
    - **commodity**: Optional filter by commodity
    - **source**: Optional filter by source

    Returns top-K similar document chunks with metadata.
    """
    start_time = time.time()

    try:
        _, _, search, _, _, _ = get_services()

        # Perform search
        results = await search.search(
            query=request.query,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            commodity=request.commodity,
            source=request.source
        )

        # Convert to response model
        search_results = [
            SearchResult(
                id=r.get('id'),
                document_id=r.get('document_id'),
                chunk_index=r.get('chunk_index'),
                chunk_text=r.get('chunk_text'),
                similarity=r.get('similarity'),
                metadata=r.get('metadata', {})
            )
            for r in results
        ]

        execution_time = (time.time() - start_time) * 1000

        logger.info(f"Search query '{request.query[:50]}...' returned {len(search_results)} results in {execution_time:.0f}ms")

        return SearchResponse(
            query=request.query,
            results=search_results,
            count=len(search_results),
            execution_time_ms=execution_time
        )

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/query", response_model=RAGResponse)
async def rag_query(request: RAGRequest):
    """
    RAG (Retrieval Augmented Generation) query endpoint.

    Combines semantic search with Perplexity AI to generate answers based on local documents.

    - **query**: Question in any language
    - **commodity**: Optional commodity context (cashew, rubber)
    - **top_k**: Number of context chunks to retrieve (1-10)
    - **use_cache**: Use cached responses if available (default: true)

    Returns AI-generated answer with citations from local and external sources.

    Cost: ~$0.005 per query (Perplexity API)
    """
    start_time = time.time()
    session_id = "default"  # TODO: Get from request headers

    try:
        _, _, search, perplexity, cache, budget = get_services()

        # Check budget
        can_execute, reason = await budget.can_execute_rag_query()
        if not can_execute:
            await budget.log_query(
                session_id=session_id,
                endpoint="/api/v1/rag/query",
                query_type="rag",
                status="rate_limited",
                error_message=reason
            )
            raise HTTPException(status_code=429, detail=reason)

        # Check cache if enabled
        cached_response = None
        if request.use_cache:
            cached_response = await cache.get(request.query, request.commodity)

        if cached_response:
            # Return cached response
            execution_time = (time.time() - start_time) * 1000

            await budget.log_query(
                session_id=session_id,
                endpoint="/api/v1/rag/query",
                query_type="rag",
                cost_usd=0.0,  # No cost for cached
                cached=True,
                execution_time_ms=execution_time
            )

            return RAGResponse(
                query=request.query,
                answer=cached_response['response'],
                citations=cached_response.get('citations', []),
                context_used=len(cached_response.get('context_used', '')),
                model=cached_response.get('metadata', {}).get('model', 'cached'),
                tokens_used=cached_response.get('metadata', {}).get('tokens_used'),
                execution_time_ms=execution_time,
                cached=True
            )

        # Step 1: Retrieve context from semantic search
        context = await search.search_with_context(
            query=request.query,
            top_k=request.top_k,
            commodity=request.commodity
        )

        context_chars = len(context)
        logger.info(f"Retrieved {context_chars} chars context for RAG query")

        # Step 2: RAG query with Perplexity
        result = await perplexity.rag_query(
            query=request.query,
            retrieved_context=context,
            commodity=request.commodity or "agricultural"
        )

        execution_time = (time.time() - start_time) * 1000

        # Cache the response
        if request.use_cache:
            await cache.set(
                query=request.query,
                response=result['response_text'],
                context_used=context,
                citations=result.get('citations', []),
                metadata=result.get('metadata', {}),
                commodity=request.commodity
            )

        # Log usage
        await budget.log_query(
            session_id=session_id,
            endpoint="/api/v1/rag/query",
            query_type="rag",
            cost_usd=0.005,  # RAG cost
            cached=False,
            execution_time_ms=execution_time
        )

        logger.info(f"RAG query '{request.query[:50]}...' completed in {execution_time:.0f}ms")

        return RAGResponse(
            query=request.query,
            answer=result['response_text'],
            citations=result.get('citations', []),
            context_used=context_chars,
            model=result['metadata']['model'],
            tokens_used=result['metadata'].get('tokens_used'),
            execution_time_ms=execution_time,
            cached=False
        )

    except HTTPException:
        raise
    except Exception as e:
        await budget.log_query(
            session_id=session_id,
            endpoint="/api/v1/rag/query",
            query_type="rag",
            status="error",
            error_message=str(e)
        )
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    session_id: str = None,
    limit: int = 10
):
    """
    Get conversation history for a session.

    - **session_id**: Optional session identifier
    - **limit**: Number of messages to return (1-100)

    Returns recent conversation messages.
    """
    try:
        supabase, _, _, _, _, _ = get_services()

        # Query conversation history from database
        query = supabase.client.table("conversation_history").select("*")

        if session_id:
            query = query.eq("session_id", session_id)

        result = query.order("created_at", desc=True).limit(limit).execute()

        messages = result.data if result.data else []

        return ConversationHistoryResponse(
            session_id=session_id or "default",
            messages=[],  # TODO: Parse messages from database
            count=len(messages)
        )

    except Exception as e:
        logger.error(f"History error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=UsageStats)
async def get_usage_stats():
    """
    Get usage statistics and budget tracking.

    Returns:
    - Total query counts (search, RAG)
    - Cache hit rates
    - Cost tracking
    - Budget utilization

    Useful for monitoring and budget management.
    """
    try:
        _, _, _, _, cache, budget = get_services()

        # Get budget stats
        budget_stats = await budget.get_current_month_stats()

        # Get cache stats
        cache_stats = cache.get_stats()

        # Calculate cache metrics
        total_queries = budget_stats.get('total_queries', 0)
        search_queries = total_queries - budget_stats.get('rag_queries', 0)
        cache_hits = cache_stats.get('total_hits', 0)
        cache_hit_rate = (cache_hits / total_queries * 100) if total_queries > 0 else 0.0

        return UsageStats(
            total_queries=total_queries,
            search_queries=search_queries,
            rag_queries=budget_stats.get('rag_queries', 0),
            cache_hits=cache_hits,
            cache_hit_rate=cache_hit_rate,
            total_cost_usd=budget_stats.get('total_cost_usd', 0.0),
            current_month_queries=total_queries,
            current_month_cost_usd=budget_stats.get('total_cost_usd', 0.0),
            budget_remaining_usd=budget_stats.get('budget_remaining_usd', 5.0),
            budget_utilization_pct=budget_stats.get('budget_utilization_pct', 0.0)
        )

    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns system status and service availability.
    """
    try:
        supabase, embedding, _, perplexity, _, _ = get_services()

        services = {
            "supabase": "ok",
            "embedding": "ok" if embedding else "error",
            "perplexity": "ok" if perplexity else "error"
        }

        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            services=services,
            version="1.0.0"
        )

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            services={"error": str(e)},
            version="1.0.0"
        )
