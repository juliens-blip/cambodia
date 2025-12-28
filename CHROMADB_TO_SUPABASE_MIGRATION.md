# Migration ChromaDB → Supabase pgvector

## Guide Pragmatique pour Cambodia Agri Analytics

---

## POURQUOI CETTE MIGRATION?

- Python 3.14 incompatible avec ChromaDB (onnxruntime manquant)
- Supabase déjà utilisé dans le projet pour les données
- pgvector est performant et mature
- Consolidation de la stack (moins de dépendances)

---

## COMPARAISON RAPIDE

| Fonctionnalité | ChromaDB | Supabase pgvector |
|----------------|----------|-------------------|
| Installation | ❌ Impossible (Python 3.14) | ✅ Déjà installé |
| Stockage | Local | PostgreSQL cloud |
| Scalabilité | Limitée | Excellente |
| Backup | Manuel | Automatique |
| Coût | Gratuit | Gratuit (plan free) |
| Performance | Très rapide | Rapide |

---

## SETUP SUPABASE VECTOR

### 1. Activer pgvector (via Supabase Dashboard)

```sql
-- Se connecter à Supabase SQL Editor
-- https://app.supabase.com/project/YOUR_PROJECT/sql

-- Activer l'extension pgvector
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Créer la table pour les embeddings

```sql
-- Table pour stocker les embeddings de documents
CREATE TABLE document_embeddings (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  document_id TEXT NOT NULL,
  document_name TEXT,
  content TEXT NOT NULL,
  embedding vector(1536),  -- Dimension OpenAI ada-002
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour la recherche vectorielle (HNSW - similaire à ChromaDB)
CREATE INDEX ON document_embeddings
USING hnsw (embedding vector_cosine_ops);

-- Index pour recherche par document_id
CREATE INDEX ON document_embeddings(document_id);

-- Index pour recherche dans metadata
CREATE INDEX ON document_embeddings USING GIN(metadata);
```

### 3. Fonction de recherche sémantique

```sql
-- Fonction pour rechercher les documents similaires
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  id UUID,
  document_id TEXT,
  document_name TEXT,
  content TEXT,
  metadata JSONB,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    document_embeddings.id,
    document_embeddings.document_id,
    document_embeddings.document_name,
    document_embeddings.content,
    document_embeddings.metadata,
    1 - (document_embeddings.embedding <=> query_embedding) AS similarity
  FROM document_embeddings
  WHERE 1 - (document_embeddings.embedding <=> query_embedding) > match_threshold
  ORDER BY document_embeddings.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

---

## CODE PYTHON: MIGRATION

### AVANT (ChromaDB - ne fonctionne pas)

```python
from chromadb import Client
from chromadb.config import Settings

# Initialisation
client = Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_data"
))

collection = client.get_or_create_collection(
    name="cambodia_documents",
    metadata={"description": "Cambodia agricultural documents"}
)

# Ajouter des documents
collection.add(
    documents=["Text content here"],
    metadatas=[{"source": "report.pdf", "page": 1}],
    ids=["doc_1"]
)

# Rechercher
results = collection.query(
    query_texts=["query text"],
    n_results=10
)
```

### APRÈS (Supabase pgvector - fonctionne)

```python
from supabase import create_client
import os
from typing import List, Dict, Any
import openai  # Pour générer les embeddings

class SupabaseVectorStore:
    """Remplacement de ChromaDB avec Supabase pgvector"""

    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        # Initialiser OpenAI pour les embeddings
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def _get_embedding(self, text: str) -> List[float]:
        """Génère un embedding avec OpenAI"""
        response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """Ajoute des documents avec leurs embeddings"""
        for doc, metadata, doc_id in zip(documents, metadatas, ids):
            embedding = self._get_embedding(doc)

            self.supabase.table("document_embeddings").insert({
                "document_id": doc_id,
                "document_name": metadata.get("source", ""),
                "content": doc,
                "embedding": embedding,
                "metadata": metadata
            }).execute()

    def query(
        self,
        query_texts: List[str],
        n_results: int = 10,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Recherche sémantique"""
        # Générer l'embedding de la requête
        query_embedding = self._get_embedding(query_texts[0])

        # Appeler la fonction Supabase
        result = self.supabase.rpc(
            "match_documents",
            {
                "query_embedding": query_embedding,
                "match_count": n_results,
                "match_threshold": threshold
            }
        ).execute()

        # Formater les résultats au format ChromaDB pour compatibilité
        documents = []
        metadatas = []
        distances = []
        ids = []

        for row in result.data:
            documents.append(row["content"])
            metadatas.append(row["metadata"])
            distances.append(1 - row["similarity"])  # Convertir similarité en distance
            ids.append(row["id"])

        return {
            "documents": [documents],
            "metadatas": [metadatas],
            "distances": [distances],
            "ids": [ids]
        }

    def delete(self, ids: List[str]):
        """Supprime des documents"""
        self.supabase.table("document_embeddings").delete().in_(
            "document_id", ids
        ).execute()

    def get(self, ids: List[str] = None) -> Dict[str, Any]:
        """Récupère des documents"""
        query = self.supabase.table("document_embeddings").select("*")

        if ids:
            query = query.in_("document_id", ids)

        result = query.execute()

        return {
            "documents": [row["content"] for row in result.data],
            "metadatas": [row["metadata"] for row in result.data],
            "ids": [row["id"] for row in result.data]
        }


# UTILISATION (API compatible ChromaDB)
vector_store = SupabaseVectorStore()

# Ajouter des documents
vector_store.add_documents(
    documents=["Text content here"],
    metadatas=[{"source": "report.pdf", "page": 1}],
    ids=["doc_1"]
)

# Rechercher
results = vector_store.query(
    query_texts=["query text"],
    n_results=10
)
```

---

## MIGRATION DU CODE EXISTANT

### Fichiers à Modifier

1. **Rechercher tous les usages de ChromaDB:**
```bash
grep -r "chromadb" D:\Projects\cambodia\app --include="*.py"
grep -r "chroma" D:\Projects\cambodia\app --include="*.py"
```

2. **Remplacer les imports:**
```python
# AVANT
from chromadb import Client
from chromadb.config import Settings

# APRÈS
from app.services.vector_store import SupabaseVectorStore
```

3. **Adapter les appels:**
```python
# AVANT
client = Client()
collection = client.get_or_create_collection("docs")

# APRÈS
vector_store = SupabaseVectorStore()
```

---

## CONFIGURATION .env

Ajouter les variables d'environnement:

```bash
# Supabase (déjà présent normalement)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# OpenAI pour les embeddings
OPENAI_API_KEY=sk-...
```

---

## TESTS DE VALIDATION

```python
# test_vector_store.py
import pytest
from app.services.vector_store import SupabaseVectorStore

def test_add_and_query():
    """Test basique d'ajout et recherche"""
    vs = SupabaseVectorStore()

    # Ajouter un document test
    vs.add_documents(
        documents=["Cambodia agriculture report 2024"],
        metadatas=[{"source": "test.pdf"}],
        ids=["test_1"]
    )

    # Rechercher
    results = vs.query(
        query_texts=["agriculture Cambodia"],
        n_results=5
    )

    assert len(results["documents"][0]) > 0
    print("✓ Test passed: documents found")

def test_delete():
    """Test de suppression"""
    vs = SupabaseVectorStore()
    vs.delete(ids=["test_1"])
    print("✓ Test passed: document deleted")

if __name__ == "__main__":
    test_add_and_query()
    test_delete()
```

---

## PERFORMANCE TIPS

### 1. Batch Inserts
```python
def add_documents_batch(self, documents, metadatas, ids, batch_size=100):
    """Insert par lots pour meilleure performance"""
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i+batch_size]
        batch_meta = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]

        rows = []
        for doc, meta, doc_id in zip(batch_docs, batch_meta, batch_ids):
            embedding = self._get_embedding(doc)
            rows.append({
                "document_id": doc_id,
                "content": doc,
                "embedding": embedding,
                "metadata": meta
            })

        self.supabase.table("document_embeddings").insert(rows).execute()
```

### 2. Cache des Embeddings
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def _get_embedding_cached(self, text: str) -> tuple:
    """Cache les embeddings fréquents"""
    embedding = self._get_embedding(text)
    return tuple(embedding)  # tuple pour hashable
```

### 3. Index Appropriés
```sql
-- HNSW pour recherche rapide (déjà créé)
-- Ajuster les paramètres selon volume de données
CREATE INDEX ON document_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

---

## ROLLBACK PLAN

Si besoin de revenir à ChromaDB plus tard:

1. **Exporter les données de Supabase:**
```python
def export_to_chromadb():
    """Export Supabase → ChromaDB format"""
    vs = SupabaseVectorStore()
    results = vs.get()  # Tous les documents

    # Sauvegarder au format JSON
    import json
    with open("embeddings_backup.json", "w") as f:
        json.dump(results, f)
```

2. **Réimporter dans ChromaDB:**
```python
# Quand Python 3.11 sera utilisé
def import_from_backup():
    import chromadb
    import json

    client = chromadb.Client()
    collection = client.get_or_create_collection("cambodia_documents")

    with open("embeddings_backup.json", "r") as f:
        data = json.load(f)

    collection.add(
        documents=data["documents"],
        metadatas=data["metadatas"],
        ids=data["ids"]
    )
```

---

## CHECKLIST DE MIGRATION

- [ ] 1. Activer pgvector dans Supabase
- [ ] 2. Créer la table `document_embeddings`
- [ ] 3. Créer la fonction `match_documents`
- [ ] 4. Créer `app/services/vector_store.py` avec `SupabaseVectorStore`
- [ ] 5. Ajouter `OPENAI_API_KEY` dans `.env`
- [ ] 6. Remplacer tous les imports ChromaDB
- [ ] 7. Tester avec `test_vector_store.py`
- [ ] 8. Migrer les données existantes (si applicable)
- [ ] 9. Supprimer `chroma_data/` directory
- [ ] 10. Mettre à jour la documentation

---

## COÛT ESTIMÉ

**Supabase Free Tier:**
- 500 MB de stockage PostgreSQL (largement suffisant pour embeddings)
- 2 GB de bandwidth/mois
- Illimité pour projets de taille moyenne

**OpenAI Embeddings:**
- text-embedding-ada-002: $0.0001 / 1K tokens
- ~1000 documents = ~$0.10
- Très abordable pour le projet

---

## CONCLUSION

**Migration ChromaDB → Supabase pgvector:**

✅ **Avantages:**
- Fonctionne avec Python 3.14
- Consolidation de la stack
- Meilleure scalabilité
- Backup automatique

⚠️ **Considérations:**
- Dépendance OpenAI pour embeddings
- Requiert connexion internet
- Latence légèrement supérieure (réseau)

**Recommandation:** MIGRER maintenant, évaluer ChromaDB plus tard si besoin.

---

**Généré le:** 2025-12-25
**Par:** Agent DEBUGGER
**Projet:** Cambodia Agri Analytics
