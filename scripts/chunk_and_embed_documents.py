"""Chunk context documents and generate embeddings (one-time setup).

This script:
1. Fetches all context documents from Supabase
2. Chunks each document into ~2048 char pieces (10% overlap)
3. Generates embeddings using multilingual-e5-large (1024 dim)
4. Stores chunks + embeddings in document_embeddings table

Expected:
- Input: 34 documents (~207K chars total)
- Output: ~110 chunks with embeddings
- Time: 5-10 minutes (CPU inference)
- Cost: $0 (local embeddings)
"""
import asyncio
import sys
import os
import io
from tqdm import tqdm

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.supabase_service import SupabaseService
from app.services.embedding_service import EmbeddingService
from app.services.chunking_service import ChunkingService


async def chunk_and_embed():
    """Main workflow: fetch → chunk → embed → store."""

    print("=" * 80)
    print("Chunk & Embed Pipeline - Phase 3")
    print("=" * 80)

    # Step 1: Initialize services
    print("\n1️⃣ Initializing services...")
    print("   - Loading multilingual-e5-large model (~2.2 GB)...")
    print("   - This may take 1-2 minutes on first run...")

    try:
        supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
        embedding = EmbeddingService()  # Downloads model on first run
        chunking = ChunkingService(chunk_size=2048, chunk_overlap=200)

        print(f"   ✅ Services initialized")
        print(f"      - Embedding model: {embedding.get_model_info()['model_name']}")
        print(f"      - Embedding dimension: {embedding.dimension}")
        print(f"      - Chunk size: {chunking.chunk_size} chars")
        print(f"      - Chunk overlap: {chunking.chunk_overlap} chars")
    except Exception as e:
        print(f"   ❌ Error initializing services: {e}")
        return False

    # Step 2: Fetch context documents
    print("\n2️⃣ Fetching context documents from Supabase...")

    try:
        docs = await supabase.get_context_documents(limit=100)
        print(f"   ✅ Fetched {len(docs)} documents")

        # Calculate statistics
        total_chars = sum(len(doc['text_content']) for doc in docs)
        avg_chars = total_chars // len(docs) if docs else 0

        print(f"      - Total characters: {total_chars:,}")
        print(f"      - Average per document: {avg_chars:,} chars")
        print(f"      - Estimated chunks: ~{total_chars // 2048 + len(docs)}")

    except Exception as e:
        print(f"   ❌ Error fetching documents: {e}")
        return False

    if not docs:
        print("   ⚠️ No documents found. Run data collection first.")
        return False

    # Step 3: Process each document
    print(f"\n3️⃣ Processing {len(docs)} documents...")
    print("   Chunking → Embedding → Storing...")

    total_chunks = 0
    failed_docs = []

    for doc in tqdm(docs, desc="Processing", unit="doc"):
        doc_id = doc['id']
        text = doc['text_content']
        title = doc.get('title', 'Untitled')[:40]

        try:
            # Build metadata
            metadata = {
                'source': doc.get('source'),
                'commodity': doc.get('commodity'),
                'title': doc.get('title'),
                'url': doc.get('url'),
                'extraction_method': doc.get('extraction_method'),
                'scraped_at': doc.get('scraped_at')
            }

            # Step 3a: Chunk document
            chunks = chunking.chunk_document(text, doc_id, metadata)

            if not chunks:
                tqdm.write(f"   ⚠️ No chunks for {title} (empty text?)")
                continue

            # Step 3b: Generate embeddings (batch)
            chunk_texts = [c['chunk_text'] for c in chunks]
            embeddings = embedding.embed_batch(
                chunk_texts,
                batch_size=32,
                show_progress=False  # Disable inner progress bar
            )

            # Step 3c: Store in Supabase
            for chunk, emb in zip(chunks, embeddings):
                try:
                    supabase.client.table("document_embeddings").insert({
                        "document_id": chunk['document_id'],
                        "chunk_index": chunk['chunk_index'],
                        "chunk_text": chunk['chunk_text'],
                        "embedding": emb,
                        "metadata": chunk['metadata']
                    }).execute()

                except Exception as e:
                    tqdm.write(f"   ❌ Error storing chunk {chunk['chunk_index']} of {title}: {e}")
                    # Continue with next chunk

            total_chunks += len(chunks)
            tqdm.write(f"   ✅ {title}: {len(chunks)} chunks ({len(text):,} chars)")

        except Exception as e:
            tqdm.write(f"   ❌ Failed: {title} - {e}")
            failed_docs.append({'title': title, 'error': str(e)})
            continue

    # Step 4: Final statistics
    print("\n" + "=" * 80)
    print("📊 Pipeline Complete - Statistics")
    print("=" * 80)

    print(f"\nDocuments processed: {len(docs)}")
    print(f"Total chunks created: {total_chunks}")
    print(f"Average chunks per document: {total_chunks / len(docs):.1f}")

    if failed_docs:
        print(f"\n⚠️ Failed documents: {len(failed_docs)}")
        for fail in failed_docs[:5]:  # Show first 5
            print(f"   - {fail['title']}: {fail['error'][:60]}")
    else:
        print(f"\n✅ All documents processed successfully!")

    # Step 5: Verify storage
    print("\n4️⃣ Verifying storage in Supabase...")

    try:
        result = supabase.client.table("document_embeddings").select("id").execute()
        stored_count = len(result.data) if result.data else 0

        print(f"   ✅ Chunks in database: {stored_count}")

        if stored_count != total_chunks:
            print(f"   ⚠️ Mismatch: Expected {total_chunks}, found {stored_count}")
        else:
            print(f"   ✅ All {total_chunks} chunks verified in database")

    except Exception as e:
        print(f"   ❌ Error verifying storage: {e}")

    print("\n" + "=" * 80)
    print("✅ Phase 3 Complete!")
    print("=" * 80)
    print("\n🚀 Ready for Phase 4: Semantic Search Testing")
    print("   Next: python scripts/test_semantic_search.py")
    print("=" * 80)

    return True


async def main():
    """Main execution."""
    try:
        success = await chunk_and_embed()

        if not success:
            print("\n❌ Pipeline failed. Check errors above.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
