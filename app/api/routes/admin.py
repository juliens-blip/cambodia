"""Admin routes for maintenance tasks."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import logging
from datetime import datetime
import re
from uuid import uuid4

from app.services.supabase_service import SupabaseService
from app.services.embedding_service import get_embedding_service
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Découpe le texte en chunks avec overlap."""
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


async def index_documents_task():
    """Background task pour indexer les documents - OPTIMISÉ pour Railway."""
    import gc
    import sys

    def log_progress(msg: str):
        """Log avec flush immédiat pour Railway."""
        logger.info(msg)
        print(msg, flush=True)

    log_progress("🚀 Starting documents indexation (background task)...")

    try:
        # Initialize services
        supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
        embedding_service = get_embedding_service()  # Singleton - no duplicate model load

        log_progress(f"✅ Embedding model ready: {embedding_service.dimension}D")

        # Fetch documents
        result = supabase.client.table("context_documents").select("*").execute()
        documents = result.data

        log_progress(f"📚 Found {len(documents)} documents to index")

        if not documents:
            log_progress("⚠️ No documents found")
            return

        # Process documents in batches to manage memory
        total_chunks = 0
        batch_size = 5  # Process 5 documents at a time

        for batch_start in range(0, len(documents), batch_size):
            batch_end = min(batch_start + batch_size, len(documents))
            batch_docs = documents[batch_start:batch_end]

            log_progress(f"📦 Processing batch {batch_start//batch_size + 1}: docs {batch_start+1}-{batch_end}")

            # Collect all chunks for this batch
            all_chunks_data = []

            for i, doc in enumerate(batch_docs, batch_start + 1):
                doc_id = doc.get('id')
                title = doc.get('title', 'Unknown')
                text = doc.get('text_content', '')
                commodity = doc.get('commodity', 'unknown')
                source = doc.get('source', 'unknown')
                url = doc.get('url')

                if not text or len(text) < 50:
                    log_progress(f"  ⏭️ [{i}/{len(documents)}] Skipping {title[:30]}: too short")
                    continue

                # Chunk text
                chunks = chunk_text(text, chunk_size=500, overlap=50)
                log_progress(f"  📄 [{i}/{len(documents)}] {title[:40]}... → {len(chunks)} chunks")

                # Generate embeddings using BATCH method (more efficient)
                try:
                    embeddings = embedding_service.embed_batch(chunks, batch_size=16, show_progress=False)
                except Exception as emb_error:
                    log_progress(f"  ❌ Embedding error for {title[:30]}: {emb_error}")
                    continue

                # Prepare data for batch insert
                for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    all_chunks_data.append({
                        'id': str(uuid4()),
                        'document_id': doc_id,
                        'chunk_index': idx,
                        'chunk_text': chunk,
                        'embedding': embedding,
                        'metadata': {
                            'source': source,
                            'commodity': commodity,
                            'title': title,
                            'url': url,
                            'chunk_count': len(chunks)
                        }
                    })

            # Batch insert all chunks from this batch of documents
            if all_chunks_data:
                try:
                    # Insert in smaller batches to avoid timeout
                    insert_batch_size = 20
                    for insert_start in range(0, len(all_chunks_data), insert_batch_size):
                        insert_batch = all_chunks_data[insert_start:insert_start + insert_batch_size]
                        supabase.client.table("document_embeddings").insert(insert_batch).execute()

                    total_chunks += len(all_chunks_data)
                    log_progress(f"  ✅ Inserted {len(all_chunks_data)} chunks (total: {total_chunks})")
                except Exception as db_error:
                    log_progress(f"  ❌ DB insert error: {db_error}")

            # Force garbage collection after each batch to free memory
            del all_chunks_data
            gc.collect()
            log_progress(f"  🧹 Memory cleaned")

        log_progress(f"🎉 Indexation complete: {len(documents)} docs, {total_chunks} chunks")

    except Exception as e:
        log_progress(f"❌ Indexation failed: {e}")
        logger.error(f"❌ Indexation failed: {e}", exc_info=True)
        raise


@router.post("/index-documents")
async def trigger_indexation(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Déclenche l'indexation des documents Google Drive en arrière-plan.

    Cette route:
    1. Récupère les documents de context_documents
    2. Les découpe en chunks
    3. Génère les embeddings
    4. Les stocke dans document_embeddings

    L'indexation se fait en background pour ne pas bloquer la requête.

    Returns:
        Message de confirmation
    """
    try:
        # Check if documents exist
        supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
        result = supabase.client.table("context_documents").select("id", count="exact").limit(1).execute()

        count = result.count if hasattr(result, 'count') else 0

        if count == 0:
            raise HTTPException(
                status_code=404,
                detail="No documents found in context_documents. Run the collector first."
            )

        # Launch background task
        background_tasks.add_task(index_documents_task)

        return {
            "status": "started",
            "message": "Document indexation started in background",
            "documents_to_index": count,
            "started_at": datetime.utcnow().isoformat(),
            "note": "Check Railway logs for progress"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting indexation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indexation-status")
async def check_indexation_status() -> Dict[str, Any]:
    """
    Vérifie le statut de l'indexation.

    Returns:
        Nombre de documents et chunks indexés
    """
    try:
        supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

        # Count documents
        docs_result = supabase.client.table("context_documents").select("id", count="exact").limit(1).execute()
        docs_count = docs_result.count if hasattr(docs_result, 'count') else 0

        # Count chunks
        chunks_result = supabase.client.table("document_embeddings").select("id", count="exact").limit(1).execute()
        chunks_count = chunks_result.count if hasattr(chunks_result, 'count') else 0

        # Sample chunk to verify
        sample = None
        if chunks_count > 0:
            sample_result = supabase.client.table("document_embeddings").select("metadata").limit(1).execute()
            if sample_result.data:
                sample = sample_result.data[0].get('metadata', {})

        return {
            "documents_in_context": docs_count,
            "chunks_indexed": chunks_count,
            "indexation_complete": chunks_count > 0,
            "sample_metadata": sample
        }

    except Exception as e:
        logger.error(f"Error checking status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear-embeddings")
async def clear_embeddings() -> Dict[str, Any]:
    """
    Supprime tous les embeddings pour ré-indexation.

    ⚠️ ATTENTION: Cette action est irréversible!

    Returns:
        Nombre d'embeddings supprimés
    """
    try:
        supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

        # Count before delete
        before = supabase.client.table("document_embeddings").select("id", count="exact").limit(1).execute()
        count_before = before.count if hasattr(before, 'count') else 0

        # Delete all
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


@router.get("/test-search")
async def test_search(query: str = "cashew market analysis", commodity: str = "cashew") -> Dict[str, Any]:
    """
    Test semantic search directly from the API.

    This bypasses Streamlit to test if search works.
    """
    try:
        from app.services.semantic_search_service import SemanticSearchService

        logger.info(f"🔍 Testing search: query='{query}', commodity='{commodity}'")

        # Initialize services - use singleton to avoid reloading model
        supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
        embedding = get_embedding_service()  # Singleton
        search = SemanticSearchService(supabase, embedding)

        logger.info(f"Embedding dimension: {embedding.dimension}")

        # Perform search
        import asyncio
        results = asyncio.get_event_loop().run_until_complete(
            search.search(
                query=query,
                top_k=5,
                similarity_threshold=0.3,
                commodity=commodity
            )
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
                for r in results[:3]  # Return first 3
            ]
        }

    except Exception as e:
        logger.error(f"Test search error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "query": query
        }
