# Phase 8: Semantic Search & RAG - Résumé Exécutif

**Date**: 2025-12-26
**Agent APEX**: ac63a3c
**Statut**: ✅ PLAN COMPLET READY

---

## 🎯 En Bref

**Système de recherche sémantique + RAG 100% GRATUIT** pour 34 documents (206K chars) utilisant:

- ✅ **Embeddings**: `multilingual-e5-large` (gratuit, local, 1024 dim)
- ✅ **Vector DB**: Supabase pgvector (alternative ChromaDB)
- ✅ **RAG LLM**: Perplexity API existante (budget: ~50 queries/mois)
- ✅ **Coût total**: ~**$0.25/mois** (seulement Perplexity RAG)

---

## 📊 Architecture Simplifiée

```
Question utilisateur
  ↓
1. Embedding local (multilingual-e5) → Vector(1024)
  ↓
2. Recherche pgvector → Top 5 chunks (similarité > 0.7)
  ↓
3. Contexte formaté → "Source 1: ...\nSource 2: ..."
  ↓
4. Perplexity RAG → Réponse avec citations
  ↓
Réponse à l'utilisateur (context + web)
```

**Durée**: <5 secondes end-to-end
**Coût**: ~$0.005 par question

---

## 🛠️ Implémentation (7 Phases, 20h)

| Phase | Durée | Livrables |
|-------|-------|-----------|
| 1. Setup Infrastructure | 2h | Migration pgvector, deps Python |
| 2. Créer Services | 4h | 4 services (embedding, chunking, search, RAG) |
| 3. Chunking & Embedding | 3h | 110 chunks embedded (34 docs) |
| 4. Semantic Search Test | 2h | Script test, validation queries |
| 5. RAG Q&A Implementation | 4h | Script RAG, tests multilingues |
| 6. Documentation | 3h | 2 guides (search, RAG) |
| 7. Production Validation | 2h | Tests end-to-end, monitoring |
| **TOTAL** | **20h** | **2.5 jours** |

---

## 💰 Budget Détaillé

### Setup (One-time)
- Embeddings (110 chunks): **$0** (local)
- Supabase pgvector: **$0** (free tier)
- Tests Perplexity: **$0.05** (10 queries)
- **TOTAL SETUP**: **$0.05**

### Récurrent (Mensuel)
- Stockage pgvector (675 KB): **$0** (free tier)
- Queries similarity search: **$0** (illimité)
- RAG Perplexity (50 queries): **$0.25**
- **TOTAL MENSUEL**: **$0.25**

### Budget Perplexity (Après Phase 8)
- Avant: 76/1000 (7.6%)
- Phase 8: +50 queries/mois
- Après: **126/1000 (12.6%)**
- Reste: **874 queries** disponibles

---

## 🔑 Décisions Techniques

### 1. Embeddings: multilingual-e5-large ⭐
**Pourquoi**:
- ✅ Gratuit (local inference)
- ✅ Multilingual (100+ langues, incluant Khmer)
- ✅ State-of-the-art (MIRACL benchmark)
- ✅ Dimension modérée (1024 vs 1536 OpenAI)

**Alternatives rejetées**:
- ❌ OpenAI text-embedding-3-small (coût $0.02/1M tokens)
- ❌ paraphrase-multilingual-MiniLM (trop léger, 384 dim)

### 2. Chunking: 512 tokens, 10% overlap
**Stratégie**:
- Taille: 512 tokens (~2048 chars/chunk)
- Overlap: 50 tokens (~200 chars)
- Séparateurs: Paragraphes → phrases → mots

**Résultat attendu**:
- 34 docs × 6,081 chars → **~110 chunks**
- Stockage: 675 KB (vectors + text)

### 3. Supabase pgvector + HNSW Index
**Configuration**:
```sql
CREATE EXTENSION vector;
CREATE TABLE document_embeddings (
  embedding vector(1024),
  ...
);
CREATE INDEX USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
```

**Performance attendue**:
- Sans HNSW: ~50ms (linear scan, 110 chunks)
- Avec HNSW: ~10ms (optimal)

### 4. Perplexity RAG (Prompt Injection)
**Méthode**:
```python
async def rag_query(query: str, context: str):
    prompt = f"""
    Context: {context}

    Question: {query}
    """
    return await perplexity._query(prompt, ...)
```

**Pas de File Upload API** (Perplexity 2025)
→ Utiliser injection contexte dans prompt (standard RAG)

---

## 📦 Services à Créer

### 1. `app/services/embedding_service.py`
```python
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer("intfloat/multilingual-e5-large")

    def embed_text(self, text: str) -> List[float]:
        return self.model.encode(f"passage: {text}").tolist()

    def embed_query(self, query: str) -> List[float]:
        return self.model.encode(f"query: {query}").tolist()
```

### 2. `app/services/chunking_service.py`
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

class ChunkingService:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=2048,
            chunk_overlap=200
        )

    def chunk_document(self, text: str) -> List[Dict]:
        return self.splitter.split_text(text)
```

### 3. `app/services/semantic_search_service.py`
```python
class SemanticSearchService:
    async def search(self, query: str, top_k: int = 5):
        # 1. Embed query
        vector = self.embedding.embed_query(query)

        # 2. pgvector similarity search
        results = self.supabase.client.rpc(
            "match_documents",
            {"query_embedding": vector, "match_count": top_k}
        ).execute()

        return results.data
```

### 4. `app/services/perplexity_service.py` (UPDATED)
```python
# Ajouter cette méthode
async def rag_query(self, query: str, context: str, commodity: str):
    prompt = f"""Context: {context}\n\nQuestion: {query}"""
    return await self._query(prompt, commodity, query_type="rag")
```

---

## 📜 Scripts CLI

### 1. `scripts/chunk_and_embed_documents.py`
**Usage**: One-time setup pour chunker + embedder 34 docs
```bash
python scripts/chunk_and_embed_documents.py
# Output: 34 docs → 110 chunks → Stored in Supabase
```

### 2. `scripts/test_semantic_search.py`
**Usage**: Tester recherche sémantique
```bash
python scripts/test_semantic_search.py
# Queries: "Cashew production", "Rubber export restrictions", etc.
```

### 3. `scripts/test_rag_qa.py`
**Usage**: Tester RAG Q&A complet
```bash
python scripts/test_rag_qa.py
# Interactive: Poser questions → Réponses avec citations
```

---

## 🧪 Validation Attendue

### Métriques Succès
- ✅ Chunking: 34 docs → 110 chunks (100%)
- ✅ Embeddings: 110 embeddings × 1024 dim (100%)
- ✅ Search: <100ms, similarity > 0.7
- ✅ RAG: <5s end-to-end, réponses précises
- ✅ Budget: +10 requêtes Perplexity (tests)

### Tests Critiques
1. **Khmer support**: Tester 5 queries en Khmer
2. **Similarity threshold**: Valider 0.7 optimal
3. **Context quality**: Top 5 chunks pertinents?
4. **RAG accuracy**: Distingue context vs web knowledge?

---

## ⚠️ Risques & Mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Khmer mal supporté | Élevé | Tester empiriquement, fallback mpnet-base |
| CPU inference lent | Moyen | Batch processing, cache embeddings |
| pgvector HNSW fail | Faible | Fallback linear scan (rapide pour 110 chunks) |
| Perplexity context dépassé | Moyen | Limiter à 5 chunks (10k chars < 128k limit) |

---

## 🚀 Prochaines Étapes

### Immédiat
1. ✅ Plan APEX complet créé
2. ⏳ **Validation utilisateur**
3. ⏳ Procéder Phase 1: Setup Infrastructure

### Après Phase 8
- **Phase 9**: Monitoring Dashboard (métriques RAG)
- **Phase 10**: Optimisations (cache, pré-compute)
- **Phase 11**: Expansion (nouvelles sources, commodities)

---

## 📚 Documentation Complète

- **Plan détaillé**: `tasks/semantic-search-rag/02_plan.md` (FULL)
- **Analyse APEX**: `tasks/semantic-search-rag/01_analysis.md`
- **Log implémentation**: `tasks/semantic-search-rag/03_implementation_log.md` (à créer)
- **Agent APEX ID**: **ac63a3c** (reprendre si besoin)

---

## ✅ Recommandation

**PROCÉDER À L'IMPLÉMENTATION**

**Pourquoi**:
- ✅ Coût négligeable ($0.25/mois)
- ✅ Budget Perplexity suffisant (874 requêtes restantes)
- ✅ Architecture solide, basée sur best practices 2025
- ✅ Plan détaillé, 20h estimées (2.5 jours)
- ✅ Valeur ajoutée ÉNORME (Q&A intelligent sur 206K chars)

**Action immédiate**:
1. Valider décisions techniques (embeddings, chunking, RAG)
2. Installer dependencies (`sentence-transformers`, `langchain`)
3. Lancer Phase 1: Setup Infrastructure (migration pgvector)

---

**Créé par**: Agent APEX Planning (ac63a3c)
**Date**: 2025-12-26
**Statut**: ✅ **READY TO EXECUTE**
**Coût total**: **~$0.25/mois**
**Durée estimée**: **2.5 jours**
