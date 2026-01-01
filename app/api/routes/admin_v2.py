"""Admin routes for maintenance tasks - V2 Railway-optimized.

This module provides document indexation that works on Railway.app by:
1. Using ThreadPoolExecutor for non-blocking embedding generation
2. Processing one chunk at a time to minimize memory spikes
3. Tracking progress via global state (queryable via /indexation-status)
4. Allowing health checks to pass during indexation

To use this instead of the original admin.py:
1. In app/main.py, change: from app.api.routes import admin
   to: from app.api.routes import admin_v2 as admin
2. Or rename this file to admin.py (backup original first)
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging
from datetime import datetime
import re
from uuid import uuid4
import asyncio
from concurrent.futures import ThreadPoolExecutor
import gc
import threading

from app.services.supabase_service import SupabaseService
from app.services.embedding_service import get_embedding_service
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Thread pool for CPU-bound embedding tasks (1 worker to control memory)
_embedding_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="embedding")

# Global indexation state for status tracking
_indexation_state = {
    "is_running": False,
    "progress": 0,
    "total": 0,
    "current_document": "",
    "chunks_created": 0,
    "errors": [],
    "started_at": None,
    "completed_at": None
}
_state_lock = threading.Lock()


def update_indexation_state(**kwargs):
    """Thread-safe update of indexation state."""
    with _state_lock:
        _indexation_state.update(kwargs)


def get_indexation_state() -> Dict[str, Any]:
    """Thread-safe read of indexation state."""
    with _state_lock:
        return _indexation_state.copy()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into chunks with overlap.

    Uses word-based chunking for better semantic coherence.
    Smaller chunks (500 words) for Railway memory constraints.
    """
    text = re.sub(r'\s+', ' ', text).strip()
    words = text.split()

    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(' '.join(chunk_words))
        start = end - overlap
        if start >= len(words):
            break

    return chunks


def embed_single_chunk_sync(chunk: str) -> List[float]:
    """
    Embed a single chunk synchronously.
    This runs in a thread pool to avoid blocking the event loop.
    """
    embedding_service = get_embedding_service()
    return embedding_service.embed_text(chunk)


async def embed_chunk_async(chunk: str) -> List[float]:
    """
    Embed a single chunk asynchronously using thread pool.
    This allows health checks to pass while embedding is in progress.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_embedding_executor, embed_single_chunk_sync, chunk)


async def index_single_document(
    supabase: SupabaseService,
    doc: Dict[str, Any],
    doc_index: int,
    total_docs: int
) -> int:
    """
    Index a single document with non-blocking embedding generation.
    Returns number of chunks created.
    """
    doc_id = doc.get('id')
    title = doc.get('title', 'Unknown')[:50]
    text = doc.get('text_content', '')
    commodity = doc.get('commodity', 'unknown')
    source = doc.get('source', 'unknown')
    url = doc.get('url')

    update_indexation_state(
        current_document=title,
        progress=doc_index
    )

    if not text or len(text) < 50:
        logger.info(f"[{doc_index}/{total_docs}] Skipping {title}: too short")
        return 0

    logger.info(f"[{doc_index}/{total_docs}] Processing: {title} ({len(text)} chars)")

    # Chunk the text
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    logger.info(f"  Created {len(chunks)} chunks")

    # Generate embeddings one at a time using async/await
    chunks_data = []
    for idx, chunk in enumerate(chunks):
        try:
            # This yields control back to event loop, allowing health checks
            embedding = await embed_chunk_async(chunk)

            chunks_data.append({
                'id': str(uuid4()),
                'document_id': doc_id,
                'chunk_index': idx,
                'chunk_text': chunk,
                'embedding': embedding,
                'metadata': {
                    'source': source,
                    'commodity': commodity,
                    'title': doc.get('title'),
                    'url': url,
                    'chunk_count': len(chunks)
                }
            })

            # Yield every 3 chunks to allow other async tasks
            if (idx + 1) % 3 == 0:
                await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"  Error embedding chunk {idx}: {e}")
            with _state_lock:
                _indexation_state["errors"].append({
                    "document": title,
                    "chunk": idx,
                    "error": str(e)
                })

    # Insert chunks in small batches
    if chunks_data:
        insert_batch_size = 20
        for i in range(0, len(chunks_data), insert_batch_size):
            batch = chunks_data[i:i + insert_batch_size]
            try:
                supabase.client.table("document_embeddings").insert(batch).execute()
            except Exception as e:
                logger.error(f"  Error inserting batch: {e}")
                with _state_lock:
                    _indexation_state["errors"].append({
                        "document": title,
                        "batch": i,
                        "error": str(e)
                    })

        logger.info(f"  Inserted {len(chunks_data)} chunks")
        with _state_lock:
            _indexation_state["chunks_created"] += len(chunks_data)

    # Cleanup
    del chunks_data
    del chunks
    gc.collect()

    return len(chunks_data) if 'chunks_data' in dir() else 0


async def run_indexation_async():
    """
    Main async indexation task.
    Uses async/await to allow health checks to pass during processing.
    """
    update_indexation_state(
        is_running=True,
        progress=0,
        total=0,
        current_document="",
        chunks_created=0,
        errors=[],
        started_at=datetime.utcnow().isoformat(),
        completed_at=None
    )

    logger.info("Starting async document indexation...")

    try:
        supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

        # Pre-load embedding model
        logger.info("Pre-loading embedding model...")
        embedding_service = get_embedding_service()
        logger.info(f"Embedding model ready: {embedding_service.dimension}D")

        # Get documents that need indexing
        indexed_result = supabase.client.table("document_embeddings") \
            .select("document_id") \
            .execute()
        indexed_ids = set(row["document_id"] for row in indexed_result.data) if indexed_result.data else set()

        docs_result = supabase.client.table("context_documents").select("*").execute()
        all_docs = docs_result.data if docs_result.data else []

        # Filter to unindexed only
        documents = [doc for doc in all_docs if doc["id"] not in indexed_ids]

        if not documents:
            logger.info("No documents to index")
            update_indexation_state(is_running=False, completed_at=datetime.utcnow().isoformat())
            return

        update_indexation_state(total=len(documents))
        logger.info(f"Found {len(documents)} documents to index")

        # Process documents one at a time
        total_chunks = 0
        for i, doc in enumerate(documents, 1):
            try:
                chunks = await index_single_document(supabase, doc, i, len(documents))
                total_chunks += chunks
                # Small delay between documents
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error processing document: {e}")
                with _state_lock:
                    _indexation_state["errors"].append({
                        "document": doc.get("title", "Unknown"),
                        "error": str(e)
                    })

        logger.info(f"Indexation complete: {len(documents)} docs, {total_chunks} chunks")

    except Exception as e:
        logger.error(f"Indexation failed: {e}", exc_info=True)
        with _state_lock:
            _indexation_state["errors"].append({"fatal": str(e)})

    finally:
        update_indexation_state(
            is_running=False,
            completed_at=datetime.utcnow().isoformat()
        )
        gc.collect()


def start_indexation_background():
    """Start indexation in a background thread with its own event loop."""
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_indexation_async())
        finally:
            loop.close()

    thread = threading.Thread(target=run_in_thread, name="IndexationThread", daemon=True)
    thread.start()
    return thread


@router.post("/index-documents")
async def trigger_indexation() -> Dict[str, Any]:
    """
    Trigger document indexation in background.

    This endpoint starts non-blocking indexation that:
    1. Fetches documents from context_documents
    2. Chunks them into smaller pieces
    3. Generates embeddings (non-blocking via ThreadPoolExecutor)
    4. Stores in document_embeddings

    Health checks continue to pass during indexation.

    Returns:
        Status and document count
    """
    state = get_indexation_state()
    if state["is_running"]:
        raise HTTPException(
            status_code=409,
            detail="Indexation is already running. Check /indexation-status for progress."
        )

    try:
        supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
        result = supabase.client.table("context_documents").select("id", count="exact").limit(1).execute()
        count = result.count if hasattr(result, 'count') else 0

        if count == 0:
            raise HTTPException(
                status_code=404,
                detail="No documents found in context_documents. Run the collector first."
            )

        # Start background indexation
        start_indexation_background()

        return {
            "status": "started",
            "message": "Document indexation started in background",
            "documents_available": count,
            "started_at": datetime.utcnow().isoformat(),
            "note": "Use /indexation-status to check progress. Health checks will pass."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting indexation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indexation-status")
async def check_indexation_status() -> Dict[str, Any]:
    """
    Check indexation status and progress.

    Returns detailed status including progress, current document, and errors.
    """
    try:
        supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

        docs_result = supabase.client.table("context_documents").select("id", count="exact").limit(1).execute()
        docs_count = docs_result.count if hasattr(docs_result, 'count') else 0

        chunks_result = supabase.client.table("document_embeddings").select("id", count="exact").limit(1).execute()
        chunks_count = chunks_result.count if hasattr(chunks_result, 'count') else 0

        state = get_indexation_state()

        sample = None
        if chunks_count > 0:
            sample_result = supabase.client.table("document_embeddings").select("metadata").limit(1).execute()
            if sample_result.data:
                sample = sample_result.data[0].get('metadata', {})

        return {
            "documents_in_context": docs_count,
            "chunks_indexed": chunks_count,
            "indexation_complete": chunks_count > 0 and not state["is_running"],
            "is_running": state["is_running"],
            "progress": {
                "current": state["progress"],
                "total": state["total"],
                "current_document": state["current_document"],
                "chunks_created_this_run": state["chunks_created"]
            },
            "started_at": state["started_at"],
            "completed_at": state["completed_at"],
            "errors": state["errors"][-5:] if state["errors"] else [],
            "sample_metadata": sample
        }

    except Exception as e:
        logger.error(f"Error checking status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear-embeddings")
async def clear_embeddings() -> Dict[str, Any]:
    """
    Delete all embeddings for re-indexation.
    WARNING: This action is irreversible!
    """
    state = get_indexation_state()
    if state["is_running"]:
        raise HTTPException(
            status_code=409,
            detail="Cannot clear embeddings while indexation is running"
        )

    try:
        supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

        before = supabase.client.table("document_embeddings").select("id", count="exact").limit(1).execute()
        count_before = before.count if hasattr(before, 'count') else 0

        supabase.client.table("document_embeddings").delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()

        logger.info(f"Deleted {count_before} embeddings")

        return {
            "status": "deleted",
            "embeddings_deleted": count_before,
            "deleted_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error deleting embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear-cache")
async def clear_search_cache() -> Dict[str, Any]:
    """Clear the semantic search cache."""
    try:
        from app.services.cache_service import get_cache_service
        cache = get_cache_service()
        cleared = 0
        if hasattr(cache, 'clear_pattern'):
            cleared = cache.clear_pattern("search:*")
        elif hasattr(cache, 'clear'):
            cache.clear()
            cleared = -1

        logger.info("Cleared search cache")

        return {
            "status": "cleared",
            "entries_cleared": cleared,
            "cleared_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return {
            "status": "warning",
            "message": f"Could not clear cache: {e}",
            "cleared_at": datetime.utcnow().isoformat()
        }


@router.get("/test-search")
async def test_search(query: str = "cashew market analysis", commodity: str = "cashew") -> Dict[str, Any]:
    """Test semantic search directly from the API."""
    try:
        from app.services.semantic_search_service import SemanticSearchService

        logger.info(f"Testing search: query='{query}', commodity='{commodity}'")

        supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
        embedding = get_embedding_service()
        search = SemanticSearchService(supabase, embedding)

        logger.info(f"Embedding dimension: {embedding.dimension}")

        results = await search.search(
            query=query,
            top_k=5,
            similarity_threshold=0.3,
            commodity=commodity
        )

        logger.info(f"Search returned {len(results)} results")

        return {
            "status": "success",
            "query": query,
            "commodity": commodity,
            "embedding_dimension": embedding.dimension,
            "results_count": len(results),
            "results": [
                {
                    "chunk_text": r.get("chunk_text", "")[:200] + "...",
                    "similarity": r.get("similarity"),
                    "metadata": r.get("metadata", {})
                }
                for r in results[:3]
            ]
        }

    except Exception as e:
        logger.error(f"Test search error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "query": query
        }


@router.post("/trigger-analysis")
async def trigger_market_analysis(
    commodity: str = None,
    force_refresh: bool = True
):
    """
    Trigger market analysis manually (admin endpoint, no rate limit).

    - **commodity**: 'cashew', 'rubber', or None for both
    - **force_refresh**: Force new analysis even if today's exists

    This endpoint bypasses the rate limiter and is intended for:
    - Manual triggers via admin scripts
    - Testing and development
    - Emergency refresh needs

    Returns:
        - status: "success" or "error"
        - results: List of analysis results per commodity
    """
    try:
        from app.services.supabase_service import SupabaseService
        from app.services.perplexity_service import PerplexityService
        from app.services.market_trends_service import MarketTrendsService

        logger.info(f"[ADMIN] Manual analysis trigger: commodity={commodity}, force_refresh={force_refresh}")

        # Initialize services
        supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
        perplexity = PerplexityService(
            api_key=settings.perplexity_api_key,
            max_requests_per_month=1000
        )
        trends = MarketTrendsService(supabase, perplexity)

        # Determine commodities to analyze
        commodities = [commodity] if commodity else ["cashew", "rubber"]
        results = []

        for comm in commodities:
            try:
                logger.info(f"[ADMIN] Analyzing {comm}...")
                result = await trends.analyze_and_store_trends(
                    commodity=comm,
                    force_refresh=force_refresh
                )
                results.append({
                    "commodity": comm,
                    "status": result.get("status"),
                    "tweet_count": result.get("tweet_count", 0),
                    "updated_at": result.get("updated_at")
                })
                logger.info(f"[ADMIN] ✅ {comm} analysis completed")
            except Exception as e:
                logger.error(f"[ADMIN] ❌ {comm} analysis failed: {e}")
                results.append({
                    "commodity": comm,
                    "status": "error",
                    "error": str(e)
                })

        success_count = sum(1 for r in results if r.get("status") == "success")

        return {
            "status": "success" if success_count > 0 else "error",
            "message": f"{success_count}/{len(commodities)} analyses completed",
            "results": results
        }

    except Exception as e:
        logger.error(f"[ADMIN] Trigger analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
