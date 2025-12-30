# Phase 3: Semantic Search & RAG System

## Overview

Phase 3 implements a production-ready semantic search and Retrieval-Augmented Generation (RAG) system for the Cambodia Agricultural Intelligence platform. The system enables multilingual Q&A over agricultural documents using state-of-the-art embedding models and vector similarity search.

## Key Features

- **Multilingual Semantic Search**: Search in Khmer, English, and Vietnamese with cross-lingual retrieval
- **Document Chunking**: Intelligent text splitting with context preservation
- **Vector Embeddings**: Using `multilingual-e5-large` (1024 dimensions)
- **Fast Vector Search**: Supabase pgvector with HNSW indexing (<100ms queries)
- **RAG Integration**: Perplexity AI integration for context-aware Q&A
- **Zero-Cost Embeddings**: Local inference using Hugging Face Transformers

**Note (production):** Railway uses `intfloat/multilingual-e5-small` (384 dimensions) for memory constraints. References to 1024D/e5-large below apply to local or optional setups.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Workflow                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  User Query      │
                    │  (Any language)  │
                    └──────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │     Embedding Service                   │
        │  multilingual-e5-large (1024 dim)       │
        │  Prefix: "query: " + text               │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   Semantic Search Service               │
        │   Supabase pgvector (HNSW index)        │
        │   Top-K retrieval (cosine similarity)   │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   Context Formatting                    │
        │   Chunk 1: [Source - Title] + text      │
        │   ---                                   │
        │   Chunk 2: [Source - Title] + text      │
        │   ...                                   │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   Perplexity RAG Service                │
        │   Model: sonar-pro                      │
        │   Context + Query → Answer              │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   Final Answer                          │
        │   - Based on local documents            │
        │   - Supplemented with online knowledge  │
        │   - Citations included                  │
        └─────────────────────────────────────────┘
```

## Quick Start

### 1. Setup and Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# .env file should include:
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
PERPLEXITY_API_KEY=your_perplexity_key
```

### 2. Chunk and Embed Documents (One-Time Setup)

```bash
# Process all context documents into chunks with embeddings
python scripts/chunk_and_embed_documents.py
```

**Expected Output:**
```
Chunk & Embed Pipeline - Phase 3
================================================================================

1. Initializing services...
   - Loading multilingual-e5-large model (~2.2 GB)...
   - Services initialized
   - Embedding model: intfloat/multilingual-e5-large
   - Embedding dimension: 1024
   - Chunk size: 2048 chars
   - Chunk overlap: 200 chars

2. Fetching context documents from Supabase...
   Fetched 34 documents
   - Total characters: 207,412
   - Average per document: 6,100 chars
   - Estimated chunks: ~110

3. Processing 34 documents...
   Chunking → Embedding → Storing...
   [Progress bar]

4. Pipeline Complete - Statistics
   Documents processed: 34
   Total chunks created: 146
   Average chunks per document: 4.3
   All chunks verified in database

Phase 3 Complete!
```

### 3. Test Semantic Search

```python
# test_semantic_search.py
import asyncio
from app.config import settings
from app.services.supabase_service import SupabaseService
from app.services.embedding_service import EmbeddingService
from app.services.semantic_search_service import SemanticSearchService

async def main():
    # Initialize services
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
    embedding = EmbeddingService()
    search = SemanticSearchService(supabase, embedding)

    # Search in any language
    results = await search.search(
        query="ការផលិតស្វាយចន្ទី",  # Khmer: "cashew production"
        top_k=5,
        commodity="cashew"
    )

    # Display results
    for result in results:
        print(f"Similarity: {result['similarity']:.4f}")
        print(f"Source: {result['metadata']['source']}")
        print(f"Title: {result['metadata']['title']}")
        print(f"Text: {result['chunk_text'][:200]}...")
        print("-" * 80)

asyncio.run(main())
```

### 4. Test RAG Workflow

```bash
# End-to-end RAG test
python scripts/test_rag_workflow.py
```

**Expected Output:**
```
RAG Workflow End-to-End Test
================================================================================

1. Initializing services...
   All services initialized

2. Test Query: "What are the main challenges for cashew production in Cambodia?"
   Commodity: cashew

3. Semantic Search - Retrieving relevant context...
   Context retrieved: 8,432 characters
   Preview: [Source 1: GDrive - iTrade Bulletin]...

4. Perplexity RAG Query - Generating answer with context...
   Query successful!
   Response length: 1,245 characters
   Citations: 3 sources
   Model: sonar-pro
   Tokens used: 2,847

5. Perplexity Response:
--------------------------------------------------------------------------------
Based on local documents and current market research, the main challenges for
cashew production in Cambodia include:

1. **Processing Capacity**: According to the iTrade Bulletin, Cambodia lacks
   sufficient cashew processing facilities, forcing farmers to export raw nuts
   at lower prices to Vietnam...

[Full answer with citations]
--------------------------------------------------------------------------------

RAG Workflow Test: COMPLETE
Ready for Production!
```

## System Metrics

### Phase 3 Implementation Summary

| Metric | Value |
|--------|-------|
| Documents processed | 34 |
| Total chunks created | 146 |
| Average chunks per document | 4.3 |
| Embedding dimension | 1024 |
| Embedding model | multilingual-e5-large |
| Vector database | Supabase pgvector |
| Index type | HNSW (m=16, ef_construction=64) |
| Query latency | <100ms (semantic search) |
| RAG latency | 2-5s (Perplexity API) |

### Cost Analysis

| Component | Cost per Query | Cost per Month (1000 queries) |
|-----------|---------------|-------------------------------|
| Embedding generation | $0 (local) | $0 |
| Supabase pgvector search | $0 (free tier) | $0 |
| Perplexity RAG API | $0.005 | $5.00 |
| **Total** | **$0.005** | **$5.00** |

## Documentation Structure

- **[README.md](README.md)** - This file (overview and quick start)
- **[USER_GUIDE.md](USER_GUIDE.md)** - How to use semantic search and RAG for Q&A
- **[TECHNICAL_REFERENCE.md](TECHNICAL_REFERENCE.md)** - Detailed API documentation
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Complete setup and configuration guide
- **[PERFORMANCE.md](PERFORMANCE.md)** - Benchmarks, optimization tips, and scaling
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[PHASE3_SUMMARY.md](PHASE3_SUMMARY.md)** - Executive summary with metrics

## Key Technologies

- **Embedding Model**: [multilingual-e5-large](https://huggingface.co/intfloat/multilingual-e5-large) by Microsoft
- **Text Splitting**: LangChain RecursiveCharacterTextSplitter
- **Vector Database**: Supabase pgvector with HNSW indexing
- **LLM for RAG**: Perplexity AI (sonar-pro model)
- **Languages Supported**: 100+ including Khmer, English, Vietnamese

## Next Steps

1. **Production Deployment**: See [SETUP_GUIDE.md](SETUP_GUIDE.md) for deployment instructions
2. **User Interface**: Integrate RAG into main application UI
3. **Monitoring**: Set up logging and performance monitoring
4. **Scaling**: See [PERFORMANCE.md](PERFORMANCE.md) for optimization strategies

## Support

For issues, questions, or contributions:
- Technical questions: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- API details: See [TECHNICAL_REFERENCE.md](TECHNICAL_REFERENCE.md)
- Setup help: See [SETUP_GUIDE.md](SETUP_GUIDE.md)

---

**Status**: Production Ready
**Last Updated**: December 26, 2024
**Version**: 1.0.0
