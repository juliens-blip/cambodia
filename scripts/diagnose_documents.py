"""
Script de diagnostic pour vérifier l'état de l'indexation des documents.

Ce script vérifie:
1. Les tables Supabase
2. Les documents dans context_documents
3. Les chunks indexés dans document_chunks
4. La fonction RPC match_documents

Usage:
    python scripts/diagnose_documents.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.supabase_service import SupabaseService
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Diagnostic complet de l'indexation des documents."""
    logger.info("🔍 Starting documents diagnostic...")

    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

    print("\n" + "="*80)
    print("DIAGNOSTIC: Documents Google Drive")
    print("="*80 + "\n")

    # 1. Vérifier context_documents
    try:
        result = supabase.client.table("context_documents").select("*", count="exact").limit(5).execute()
        count = result.count if hasattr(result, 'count') else len(result.data)
        print(f"✅ Table 'context_documents': {count} documents trouvés")

        if result.data:
            print("\n📄 Exemples de documents:")
            for i, doc in enumerate(result.data[:3], 1):
                title = doc.get('title', 'Sans titre')
                source = doc.get('source', 'Unknown')
                chars = doc.get('char_count', 0)
                print(f"   {i}. {title[:60]}... ({source}, {chars} chars)")
        else:
            print("⚠️  Aucun document trouvé dans context_documents")
            print("   → Les documents Google Drive n'ont pas encore été collectés")
    except Exception as e:
        print(f"❌ Erreur table 'context_documents': {e}")
        print("   → La table n'existe peut-être pas encore")

    # 2. Vérifier document_chunks
    try:
        result = supabase.client.table("document_chunks").select("*", count="exact").limit(1).execute()
        count = result.count if hasattr(result, 'count') else len(result.data)
        print(f"\n✅ Table 'document_chunks': {count} chunks indexés")

        if count == 0:
            print("⚠️  Aucun chunk indexé")
            print("   → Les embeddings n'ont pas été générés")
    except Exception as e:
        print(f"\n❌ Erreur table 'document_chunks': {e}")
        print("   → La table n'existe probablement pas")
        print("   → Migration requise pour créer document_chunks avec pgvector")

    # 3. Vérifier la fonction RPC match_documents
    try:
        # Test avec un vecteur factice
        test_vector = [0.1] * 384  # Dimension du modèle multilingual-e5-small
        result = supabase.client.rpc(
            "match_documents",
            {
                "query_embedding": test_vector,
                "match_count": 1,
                "match_threshold": 0.5
            }
        ).execute()
        print(f"\n✅ Fonction RPC 'match_documents': OK")
    except Exception as e:
        print(f"\n❌ Fonction RPC 'match_documents': {e}")
        print("   → La fonction RPC n'existe pas")
        print("   → Migration SQL requise")

    # 4. Résumé et recommandations
    print("\n" + "="*80)
    print("RECOMMANDATIONS")
    print("="*80 + "\n")

    print("Pour indexer les documents Google Drive, il faut:")
    print("1. ✅ Créer la table document_chunks avec pgvector (migration SQL)")
    print("2. ✅ Créer la fonction RPC match_documents (migration SQL)")
    print("3. ✅ Exécuter le collector Google Drive")
    print("4. ✅ Générer les embeddings et stocker dans document_chunks")

    print("\n📝 Prochaines étapes:")
    print("   → Je vais créer les migrations SQL nécessaires")
    print("   → Puis exécuter le script d'indexation")


if __name__ == "__main__":
    asyncio.run(main())
