#!/usr/bin/env python3
"""
Railway-optimized document indexation script.

This script is designed to run as a standalone process on Railway.app with:
- Limited memory (512MB)
- No blocking of the main API
- Resume capability after interruption
- Progress tracking in Supabase

Usage:
    # Run locally
    python scripts/index_documents_railway.py

    # On Railway via cron or one-off dyno
    python scripts/index_documents_railway.py --batch-size 3 --delay 2

Key optimizations:
1. Processes documents one at a time (no batch loading)
2. Generates embeddings one chunk at a time (minimal memory)
3. Aggressive garbage collection between documents
4. Stores progress in Supabase for resume capability
5. Small batch inserts to Supabase (20 chunks at a time)
"""

import os
import sys
import gc
import time
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4
import re

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into chunks with overlap.

    Using smaller chunks (500 words) for Railway to reduce memory per embedding.
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


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0


class RailwayIndexer:
    """
    Memory-efficient document indexer for Railway.app.

    Key features:
    - Lazy model loading (only loads when needed)
    - Single document processing (no batch loading)
    - Single chunk embedding (minimal memory spikes)
    - Progress tracking in Supabase
    - Resume capability
    """

    def __init__(
        self,
        batch_size: int = 3,
        delay_between_docs: float = 1.0,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        self.batch_size = batch_size
        self.delay_between_docs = delay_between_docs
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Lazy-loaded services
        self._supabase = None
        self._embedding = None

        # Stats
        self.stats = {
            "documents_processed": 0,
            "chunks_created": 0,
            "errors": [],
            "start_time": None,
            "end_time": None
        }

    @property
    def supabase(self):
        """Lazy-load Supabase client."""
        if self._supabase is None:
            from app.config import settings
            from app.services.supabase_service import SupabaseService
            logger.info("Initializing Supabase client...")
            self._supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
            logger.info("Supabase client ready")
        return self._supabase

    @property
    def embedding(self):
        """Lazy-load embedding service (singleton)."""
        if self._embedding is None:
            logger.info("Loading embedding model (this may take 30-60s)...")
            logger.info(f"Current memory: {get_memory_usage_mb():.1f} MB")

            from app.services.embedding_service import get_embedding_service
            self._embedding = get_embedding_service()

            logger.info(f"Embedding model loaded: {self._embedding.dimension}D")
            logger.info(f"Memory after model load: {get_memory_usage_mb():.1f} MB")
        return self._embedding

    def get_documents_to_index(self) -> List[Dict[str, Any]]:
        """
        Get list of documents that need indexing.

        Returns documents from context_documents that don't have embeddings yet.
        """
        logger.info("Fetching documents to index...")

        # Get all document IDs that already have embeddings
        indexed_result = self.supabase.client.table("document_embeddings") \
            .select("document_id") \
            .execute()

        indexed_ids = set(row["document_id"] for row in indexed_result.data) if indexed_result.data else set()
        logger.info(f"Found {len(indexed_ids)} already indexed documents")

        # Get all documents
        docs_result = self.supabase.client.table("context_documents") \
            .select("id, title, text_content, commodity, source, url") \
            .execute()

        all_docs = docs_result.data if docs_result.data else []
        logger.info(f"Found {len(all_docs)} total documents")

        # Filter to only unindexed documents
        unindexed = [doc for doc in all_docs if doc["id"] not in indexed_ids]
        logger.info(f"Documents to index: {len(unindexed)}")

        return unindexed

    def process_single_document(self, doc: Dict[str, Any]) -> int:
        """
        Process a single document: chunk -> embed -> store.

        Returns number of chunks created.
        """
        doc_id = doc["id"]
        title = doc.get("title", "Unknown")[:50]
        text = doc.get("text_content", "")
        commodity = doc.get("commodity", "unknown")
        source = doc.get("source", "unknown")
        url = doc.get("url")

        if not text or len(text) < 50:
            logger.warning(f"Skipping {title}: text too short ({len(text)} chars)")
            return 0

        logger.info(f"Processing: {title} ({len(text)} chars)")

        # Step 1: Chunk the text
        chunks = chunk_text(text, self.chunk_size, self.chunk_overlap)
        logger.info(f"  Created {len(chunks)} chunks")

        # Step 2: Generate embeddings ONE AT A TIME (memory efficient)
        chunks_data = []
        for idx, chunk in enumerate(chunks):
            try:
                # Generate single embedding
                embedding = self.embedding.embed_text(chunk)

                chunks_data.append({
                    "id": str(uuid4()),
                    "document_id": doc_id,
                    "chunk_index": idx,
                    "chunk_text": chunk,
                    "embedding": embedding,
                    "metadata": {
                        "source": source,
                        "commodity": commodity,
                        "title": doc.get("title"),
                        "url": url,
                        "chunk_count": len(chunks)
                    }
                })

                # Log progress every 5 chunks
                if (idx + 1) % 5 == 0:
                    logger.info(f"  Embedded {idx + 1}/{len(chunks)} chunks")

            except Exception as e:
                logger.error(f"  Error embedding chunk {idx}: {e}")
                self.stats["errors"].append({
                    "document": title,
                    "chunk": idx,
                    "error": str(e)
                })

        # Step 3: Insert chunks in small batches
        if chunks_data:
            insert_batch_size = 20
            for i in range(0, len(chunks_data), insert_batch_size):
                batch = chunks_data[i:i + insert_batch_size]
                try:
                    self.supabase.client.table("document_embeddings").insert(batch).execute()
                except Exception as e:
                    logger.error(f"  Error inserting batch: {e}")
                    self.stats["errors"].append({
                        "document": title,
                        "batch_start": i,
                        "error": str(e)
                    })

            logger.info(f"  Inserted {len(chunks_data)} chunks")

        # Cleanup
        del chunks_data
        del chunks
        gc.collect()

        return len(chunks_data) if chunks_data else 0

    def run(self, max_documents: Optional[int] = None) -> Dict[str, Any]:
        """
        Run the indexation process.

        Args:
            max_documents: Maximum number of documents to process (None = all)

        Returns:
            Statistics dictionary
        """
        self.stats["start_time"] = datetime.utcnow().isoformat()
        logger.info("=" * 60)
        logger.info("Railway Document Indexer - Starting")
        logger.info("=" * 60)
        logger.info(f"Memory at start: {get_memory_usage_mb():.1f} MB")

        # Get documents to index
        documents = self.get_documents_to_index()

        if not documents:
            logger.info("No documents to index. Exiting.")
            self.stats["end_time"] = datetime.utcnow().isoformat()
            return self.stats

        # Limit if specified
        if max_documents:
            documents = documents[:max_documents]
            logger.info(f"Limited to {max_documents} documents")

        # Process documents
        total = len(documents)
        for i, doc in enumerate(documents, 1):
            logger.info(f"\n[{i}/{total}] Processing document...")

            try:
                chunks_created = self.process_single_document(doc)
                self.stats["documents_processed"] += 1
                self.stats["chunks_created"] += chunks_created

            except Exception as e:
                logger.error(f"Error processing document: {e}")
                self.stats["errors"].append({
                    "document": doc.get("title", "Unknown"),
                    "error": str(e)
                })

            # Memory check and cleanup
            mem_usage = get_memory_usage_mb()
            logger.info(f"Memory: {mem_usage:.1f} MB")

            if mem_usage > 450:  # Warning threshold for 512MB limit
                logger.warning("High memory usage! Running aggressive cleanup...")
                gc.collect()
                time.sleep(2)  # Give time for memory to be released

            # Delay between documents to prevent CPU throttling
            if i < total and self.delay_between_docs > 0:
                logger.info(f"Waiting {self.delay_between_docs}s before next document...")
                time.sleep(self.delay_between_docs)

        self.stats["end_time"] = datetime.utcnow().isoformat()

        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("Indexation Complete!")
        logger.info("=" * 60)
        logger.info(f"Documents processed: {self.stats['documents_processed']}")
        logger.info(f"Chunks created: {self.stats['chunks_created']}")
        logger.info(f"Errors: {len(self.stats['errors'])}")
        logger.info(f"Final memory: {get_memory_usage_mb():.1f} MB")

        return self.stats


def main():
    parser = argparse.ArgumentParser(
        description="Railway-optimized document indexation"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=3,
        help="Number of documents to process before cleanup (default: 3)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between documents (default: 1.0)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Chunk size in words (default: 500)"
    )
    parser.add_argument(
        "--max-documents",
        type=int,
        default=None,
        help="Maximum documents to process (default: all)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check documents without processing"
    )

    args = parser.parse_args()

    if args.dry_run:
        logger.info("Dry run mode - checking documents only")
        from app.config import settings
        from app.services.supabase_service import SupabaseService

        supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

        # Count documents
        docs = supabase.client.table("context_documents").select("id", count="exact").execute()
        chunks = supabase.client.table("document_embeddings").select("id", count="exact").execute()

        logger.info(f"Context documents: {docs.count}")
        logger.info(f"Existing embeddings: {chunks.count}")
        return

    # Run indexer
    indexer = RailwayIndexer(
        batch_size=args.batch_size,
        delay_between_docs=args.delay,
        chunk_size=args.chunk_size
    )

    try:
        stats = indexer.run(max_documents=args.max_documents)

        # Exit with error code if there were errors
        if stats["errors"]:
            logger.warning(f"Completed with {len(stats['errors'])} errors")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user. Progress is saved in Supabase.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
