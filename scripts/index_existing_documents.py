"""
Script pour indexer les documents Google Drive existants dans Supabase.

Ce script:
1. Récupère les 34 documents de context_documents
2. Les découpe en chunks de 500 mots
3. Génère les embeddings (1024D avec multilingual-e5-small)
4. Les stocke dans document_embeddings

Usage:
    python scripts/index_existing_documents.py
"""
import asyncio
import sys
import os
import re
from typing import List, Dict, Any
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.supabase_service import SupabaseService
from app.services.embedding_service import EmbeddingService
from app.config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Découpe le texte en chunks avec overlap.

    Args:
        text: Texte à découper
        chunk_size: Taille des chunks en mots
        overlap: Overlap entre chunks en mots

    Returns:
        Liste de chunks de texte
    """
    # Nettoyer le texte
    text = re.sub(r'\s+', ' ', text).strip()

    # Découper en mots
    words = text.split()

    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(' '.join(chunk_words))

        # Avancer avec overlap
        start = end - overlap
        if start >= len(words):
            break

    return chunks


async def index_document(
    supabase: SupabaseService,
    embedding_service: EmbeddingService,
    document: Dict[str, Any]
) -> int:
    """
    Indexe un document en créant ses embeddings.

    Args:
        supabase: Service Supabase
        embedding_service: Service d'embedding
        document: Document à indexer

    Returns:
        Nombre de chunks créés
    """
    doc_id = document.get('id')
    title = document.get('title', 'Unknown')
    text = document.get('text_content', '')
    commodity = document.get('commodity', 'unknown')
    source = document.get('source', 'unknown')
    url = document.get('url')

    if not text or len(text) < 50:
        logger.warning(f"Skipping document {title}: text too short ({len(text)} chars)")
        return 0

    # Découper en chunks
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    logger.info(f"Document '{title[:50]}...': {len(chunks)} chunks")

    # Générer embeddings pour tous les chunks
    try:
        embeddings = []
        for chunk in chunks:
            emb = embedding_service.embed_text(chunk)
            embeddings.append(emb)

        logger.info(f"Generated {len(embeddings)} embeddings")
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return 0

    # Stocker dans document_embeddings
    stored_count = 0
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        try:
            # Préparer les données
            chunk_data = {
                'id': str(uuid4()),
                'document_id': doc_id,
                'chunk_index': i,
                'chunk_text': chunk,
                'embedding': embedding,
                'metadata': {
                    'source': source,
                    'commodity': commodity,
                    'title': title,
                    'url': url,
                    'chunk_count': len(chunks)
                }
            }

            # Insérer dans Supabase
            result = supabase.client.table("document_embeddings").insert(chunk_data).execute()

            if result.data:
                stored_count += 1

        except Exception as e:
            logger.error(f"Error storing chunk {i}: {e}")
            continue

    logger.info(f"✅ Stored {stored_count}/{len(chunks)} chunks for '{title[:40]}...'")
    return stored_count


async def main():
    """Indexe tous les documents Google Drive."""
    logger.info("🚀 Starting documents indexation...")

    # Initialize services
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
    embedding_service = EmbeddingService()

    logger.info(f"Embedding model dimension: {embedding_service.dimension}")

    # Récupérer tous les documents
    logger.info("📥 Fetching documents from context_documents...")
    result = supabase.client.table("context_documents").select("*").execute()
    documents = result.data

    logger.info(f"Found {len(documents)} documents to index")

    if not documents:
        logger.warning("No documents found in context_documents")
        return

    # Vérifier si des embeddings existent déjà
    existing = supabase.client.table("document_embeddings").select("id").limit(1).execute()
    if existing.data:
        logger.warning(f"⚠️  document_embeddings already contains data")
        response = input("Delete existing embeddings and re-index? (yes/no): ")
        if response.lower() == 'yes':
            logger.info("Deleting existing embeddings...")
            supabase.client.table("document_embeddings").delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()

    # Indexer chaque document
    total_chunks = 0
    for i, doc in enumerate(documents, 1):
        logger.info(f"\n[{i}/{len(documents)}] Indexing: {doc.get('title', 'Unknown')[:60]}...")
        chunks_created = await index_document(supabase, embedding_service, doc)
        total_chunks += chunks_created

    # Résumé
    print("\n" + "="*80)
    print("✅ INDEXATION COMPLETE")
    print("="*80)
    print(f"Documents indexés: {len(documents)}")
    print(f"Chunks créés: {total_chunks}")
    print(f"Dimension: {embedding_service.dimension}")
    print("\nLa recherche sémantique devrait maintenant fonctionner!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
