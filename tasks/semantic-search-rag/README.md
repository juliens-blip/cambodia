# Phase 8: Semantic Search & RAG System

**Date de démarrage**: 2025-12-26
**Modèle**: Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
**Agent APEX ID**: ac63a3c
**Statut**: 📋 PLANIFICATION COMPLÈTE

---

## 🎯 Objectif

Implémenter un système de **recherche sémantique** et **RAG (Retrieval Augmented Generation)** 100% GRATUIT utilisant:

- **Embeddings**: `multilingual-e5-large` (Hugging Face, local, gratuit)
- **Vector DB**: Supabase pgvector (alternative ChromaDB)
- **RAG LLM**: Perplexity API existante (PAS OpenAI)
- **Coût**: ~$0.25/mois (Perplexity RAG queries uniquement)

---

## 📊 Contexte

### Phase 7 Complétée ✅
- 34 documents contextes stockés (Supabase `context_documents`)
- 206,761 caractères de contenu
- Sources: GDrive (25 docs), ODC (8 docs)
- Langues: Khmer, English, Vietnamese
- Extraction: OCR (Tesseract)

### Contraintes Utilisateur 🔴
1. **"le moins cher"** → Utiliser options GRATUITES
2. **"j'ai deja une api perpexity connecté"** → Utiliser Perplexity pour RAG
3. ChromaDB bloqué (Python 3.14+) → Utiliser Supabase pgvector

---

## 📁 Structure

```
tasks/semantic-search-rag/
├── README.md                    # Ce fichier
├── 01_analysis.md              # Analyse APEX (A)
├── 02_plan.md                  # Plan APEX (P) ⭐
└── 03_implementation_log.md    # Log exécution APEX (E)
```

---

## 🚀 Plan d'Implémentation

**Durée estimée**: 20h (2.5 jours)
**Budget**: ~$0.25/mois (Perplexity RAG)

### 7 Phases

1. **Setup Infrastructure** (2h)
   - Migration pgvector Supabase
   - Install dependencies Python

2. **Créer Services** (4h)
   - `embedding_service.py` (multilingual-e5-large)
   - `chunking_service.py` (LangChain)
   - `semantic_search_service.py` (pgvector)
   - `perplexity_service.py` (méthode RAG)

3. **Chunking & Embedding** (3h)
   - Script `chunk_and_embed_documents.py`
   - 34 docs → ~110 chunks

4. **Semantic Search Test** (2h)
   - Script `test_semantic_search.py`
   - Validation queries

5. **RAG Q&A Implementation** (4h)
   - Script `test_rag_qa.py`
   - Tests multilingues

6. **Documentation** (3h)
   - `SEMANTIC_SEARCH_GUIDE.md`
   - `RAG_USAGE.md`

7. **Production Validation** (2h)
   - Tests end-to-end
   - Monitoring budget

---

## 📚 Livrables Attendus

### Code
- [x] `app/services/embedding_service.py`
- [x] `app/services/chunking_service.py`
- [x] `app/services/semantic_search_service.py`
- [x] `app/services/perplexity_service.py` (méthode `rag_query()`)
- [x] `supabase/migrations/003_pgvector_setup.sql`
- [x] `scripts/chunk_and_embed_documents.py`
- [x] `scripts/test_semantic_search.py`
- [x] `scripts/test_rag_qa.py`

### Documentation
- [x] `tasks/semantic-search-rag/01_analysis.md`
- [x] `tasks/semantic-search-rag/02_plan.md` ⭐
- [ ] `tasks/semantic-search-rag/03_implementation_log.md`
- [ ] `docs/SEMANTIC_SEARCH_GUIDE.md`
- [ ] `docs/RAG_USAGE.md`

---

## 💡 Décisions Clés

### Embeddings: multilingual-e5-large ✅
- **Dimension**: 1024
- **Langues**: 100+ (Khmer, English, Vietnamese)
- **Coût**: $0 (local)
- **Performance**: State-of-the-art multilingual

### Chunking: 512 tokens, 10% overlap ✅
- **Taille**: ~2048 chars/chunk
- **Overlap**: 200 chars
- **Estimé**: 110 chunks (34 docs)

### Vector DB: Supabase pgvector ✅
- **Index**: HNSW (m=16, ef_construction=64)
- **Stockage**: 675 KB (free tier OK)

### RAG LLM: Perplexity API ✅
- **Méthode**: Prompt injection
- **Budget**: ~50 queries/mois (~$0.25)

---

## 📖 Documentation Complète

- **Plan détaillé**: `02_plan.md` (architecture, workflows, code)
- **Analyse APEX**: `01_analysis.md` (alternatives, risques)
- **Agent ID**: ac63a3c (pour reprendre si besoin)

---

## ✅ Prochaines Étapes

1. Lire `02_plan.md` pour architecture détaillée
2. Valider décisions techniques avec utilisateur
3. Procéder à l'implémentation (Phase EXECUTE)
4. Logger dans `03_implementation_log.md`

---

**Créé par**: APEX Planning Agent (ac63a3c)
**Date**: 2025-12-26
**Statut**: 📋 READY FOR EXECUTION
