# Setup Guide: Phase 3 Semantic Search & RAG

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Initial Data Processing](#initial-data-processing)
5. [Service Configuration](#service-configuration)
6. [Testing](#testing)
7. [Production Deployment](#production-deployment)
8. [Maintenance](#maintenance)

## Prerequisites

### System Requirements

**Minimum:**
- Python 3.11+
- 8 GB RAM
- 5 GB disk space (for model cache)
- Internet connection (for initial model download)

**Recommended:**
- Python 3.11+
- 16 GB RAM
- 10 GB disk space
- GPU (optional, for faster embeddings)

### API Keys Required

1. **Supabase**
   - Create account at [supabase.com](https://supabase.com)
   - Create new project
   - Get URL and anon key from project settings

2. **Perplexity AI**
   - Create account at [perplexity.ai](https://www.perplexity.ai)
   - Get API key from dashboard
   - Note: Free tier = 1000 requests/month

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd cambodia
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install all requirements
pip install -r requirements.txt

# Key packages:
# - sentence-transformers (embedding model)
# - langchain-text-splitters (chunking)
# - supabase (database client)
# - httpx (Perplexity API)
```

**Expected installation time:** 5-10 minutes

### 4. Configure Environment Variables

Create `.env` file in project root:

```bash
# .env file
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Perplexity API
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxx

# Optional: Model Configuration
EMBEDDING_MODEL=intfloat/multilingual-e5-large
CHUNK_SIZE=2048
CHUNK_OVERLAP=200
```

**Security Note:** Never commit `.env` to version control!

### 5. Download Embedding Model (First Run)

```bash
# Test model download
python -c "from app.services.embedding_service import EmbeddingService; EmbeddingService()"
```

**Expected output:**
```
Loading embedding model: intfloat/multilingual-e5-large
Downloading (on first run): 100%|████████| 2.2GB/2.2GB
Model loaded successfully: 1024 dimensions
```

**Model cache location:**
- Windows: `C:\Users\<username>\.cache\huggingface\hub`
- Linux/Mac: `~/.cache/huggingface/hub`

**Download time:** 5-15 minutes (depends on internet speed)

## Database Setup

### 1. Enable pgvector Extension

In Supabase SQL Editor:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 2. Create document_embeddings Table

```sql
-- Create table for document chunks + embeddings
CREATE TABLE IF NOT EXISTS document_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES context_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1024) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes
CREATE INDEX idx_document_embeddings_doc_id
    ON document_embeddings(document_id);

CREATE INDEX idx_document_embeddings_metadata
    ON document_embeddings USING GIN(metadata);
```

### 3. Create HNSW Vector Index

**IMPORTANT:** Only create HNSW index AFTER inserting embeddings!

```sql
-- Create HNSW index for fast similarity search
-- m=16: max connections per layer (higher = better recall, slower build)
-- ef_construction=64: build-time accuracy (higher = better index, slower build)
CREATE INDEX idx_embedding_hnsw
    ON document_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

**Performance:**
- Without index: 1-5 seconds per query
- With HNSW index: <100ms per query

**Build time:** ~1-2 minutes for 146 chunks

### 4. Create match_documents RPC Function

```sql
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding VECTOR(1024),
    match_count INTEGER DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.7,
    filter_commodity TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    chunk_index INTEGER,
    chunk_text TEXT,
    similarity FLOAT,
    metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        de.id,
        de.document_id,
        de.chunk_index,
        de.chunk_text,
        1 - (de.embedding <=> query_embedding) AS similarity,
        de.metadata
    FROM document_embeddings de
    WHERE
        (1 - (de.embedding <=> query_embedding)) >= match_threshold
        AND (filter_commodity IS NULL OR de.metadata->>'commodity' = filter_commodity)
    ORDER BY de.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

**Test the function:**
```sql
-- Generate test vector (all zeros)
SELECT match_documents(
    query_embedding := ARRAY_FILL(0::float, ARRAY[1024])::vector,
    match_count := 3,
    match_threshold := 0.5
);
```

### 5. Verify Database Setup

```bash
# Run verification script
python -c "
from app.services.supabase_service import SupabaseService
from app.config import settings

supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

# Test connection
result = supabase.client.table('context_documents').select('id').limit(1).execute()
print(f'✅ Supabase connected: {len(result.data)} documents')

# Check embeddings table
result = supabase.client.table('document_embeddings').select('id').limit(1).execute()
print(f'✅ Embeddings table exists: {len(result.data)} chunks')
"
```

## Initial Data Processing

### 1. Verify Context Documents

```bash
# Check document count
python scripts/check_context_documents.py
```

**Expected output:**
```
Context Documents in Supabase
==============================
Total documents: 34
- GDrive: 20 documents
- ODC: 8 documents
- Other: 6 documents

Commodities:
- Cashew: 18 documents
- Rubber: 16 documents

Total characters: 207,412
Average per document: 6,100 chars
```

If no documents found, run Phase 1 & 2 data collection first.

### 2. Chunk and Embed All Documents

```bash
# Run chunking and embedding pipeline
python scripts/chunk_and_embed_documents.py
```

**Expected workflow:**
```
================================================================================
Chunk & Embed Pipeline - Phase 3
================================================================================

1. Initializing services...
   - Loading multilingual-e5-large model (~2.2 GB)...
   ✅ Services initialized
   - Embedding model: intfloat/multilingual-e5-large
   - Embedding dimension: 1024
   - Chunk size: 2048 chars
   - Chunk overlap: 200 chars

2. Fetching context documents from Supabase...
   ✅ Fetched 34 documents
   - Total characters: 207,412
   - Average per document: 6,100 chars
   - Estimated chunks: ~110

3. Processing 34 documents...
   Chunking → Embedding → Storing...
   100%|████████████████████████████████████| 34/34 [05:23<00:00,  9.51s/doc]

4. Pipeline Complete - Statistics
   Documents processed: 34
   Total chunks created: 146
   Average chunks per document: 4.3
   ✅ All documents processed successfully!

5. Verifying storage in Supabase...
   ✅ Chunks in database: 146
   ✅ All 146 chunks verified in database

================================================================================
✅ Phase 3 Complete!
================================================================================
```

**Processing time:** 5-10 minutes (CPU) or 2-3 minutes (GPU)

**Storage used:**
- Supabase: ~2 MB (text + embeddings)
- Disk cache: ~2.2 GB (model)

### 3. Create HNSW Index (Post-Processing)

After all embeddings are inserted, create the HNSW index:

```sql
-- Create index (run in Supabase SQL Editor)
CREATE INDEX idx_embedding_hnsw
    ON document_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

**Build time:** 1-2 minutes for 146 vectors

**Verification:**
```sql
-- Check index exists
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'document_embeddings';
```

## Service Configuration

### EmbeddingService Configuration

**Default configuration (recommended):**
```python
from app.services.embedding_service import EmbeddingService

embedding = EmbeddingService()  # Uses multilingual-e5-large
```

**Custom model:**
```python
embedding = EmbeddingService(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    # Note: Different models have different dimensions!
    # You'll need to update vector(1024) in database schema
)
```

**GPU acceleration (if available):**
```python
import torch

# Check GPU availability
print(f"GPU available: {torch.cuda.is_available()}")

# EmbeddingService automatically uses GPU if available
embedding = EmbeddingService()  # Will use GPU if CUDA is installed
```

### ChunkingService Configuration

**Default configuration (recommended):**
```python
from app.services.chunking_service import ChunkingService

chunking = ChunkingService()  # 2048 chars, 200 overlap
```

**Custom configuration:**
```python
chunking = ChunkingService(
    chunk_size=1024,      # Smaller chunks
    chunk_overlap=100,    # Less overlap
    separators=[          # Custom separators
        "\n\n",          # Paragraphs
        "\n",            # Lines
        ". ",            # Sentences
        " ",             # Words
        ""               # Characters
    ]
)
```

**Configuration guidelines:**
- **chunk_size**: 1024-4096 chars (2048 recommended)
- **chunk_overlap**: 5-15% of chunk_size (10% recommended)
- Larger chunks = more context, but less precise retrieval
- Smaller chunks = more precise, but less context

### SemanticSearchService Configuration

**Default similarity thresholds:**
```python
from app.services.semantic_search_service import SemanticSearchService

search = SemanticSearchService(supabase, embedding)

# Adjust thresholds based on use case
results = await search.search(
    query="...",
    similarity_threshold=0.7,  # Default: good balance
    # 0.8+ = Very strict (high precision, low recall)
    # 0.7 = Balanced (recommended)
    # 0.6 = Permissive (low precision, high recall)
    top_k=5
)
```

### PerplexityService Configuration

**Rate limiting:**
```python
from app.services.perplexity_service import PerplexityService

perplexity = PerplexityService(
    api_key=settings.perplexity_api_key,
    max_requests_per_month=1000  # Adjust based on plan
)
```

**Monthly reset (recommended):**
```python
# Add to cron job or scheduler
from datetime import datetime

if datetime.now().day == 1:
    perplexity.reset_counter()
```

## Testing

### 1. Test Embedding Service

```bash
# Test embeddings
python -c "
from app.services.embedding_service import EmbeddingService

embedding = EmbeddingService()

# Test query embedding
vec = embedding.embed_query('test')
print(f'✅ Embedding dimension: {len(vec)}')

# Test similarity
vec1 = embedding.embed_query('cashew')
vec2 = embedding.embed_query('ស្វាយចន្ទី')  # Khmer: cashew
sim = embedding.cosine_similarity(vec1, vec2)
print(f'✅ Cross-lingual similarity: {sim:.4f}')
"
```

### 2. Test Semantic Search

```bash
# Run semantic search test
python scripts/test_semantic_search.py
```

**Expected output:**
```
Semantic Search Test
====================
Query: cashew production

Top 5 Results:
[1] Similarity: 0.8538
    Source: GDrive - iTrade Bulletin Q2 2024
    Text: Cashew production in Cambodia has increased...

[2] Similarity: 0.8215
    Source: ODC - Agricultural Report
    Text: Kampong Thom province is the leading...

...

✅ Semantic search working correctly!
```

### 3. Test RAG Workflow

```bash
# End-to-end RAG test
python scripts/test_rag_workflow.py
```

**Expected output:**
```
RAG Workflow End-to-End Test
================================================================================

1. Initializing services...
   ✅ All services initialized

2. Test Query: "What are the main challenges for cashew production in Cambodia?"
   Commodity: cashew

3. Semantic Search - Retrieving relevant context...
   ✅ Context retrieved: 8,432 characters

4. Perplexity RAG Query - Generating answer with context...
   ✅ Query successful!
   Response length: 1,245 characters
   Citations: 3 sources
   Model: sonar-pro
   Tokens used: 2,847

5. Perplexity Response:
--------------------------------------------------------------------------------
[AI-generated answer based on local documents]
--------------------------------------------------------------------------------

================================================================================
RAG Workflow Test: COMPLETE
Ready for Production!
================================================================================
```

### 4. Run All Tests

```bash
# Run comprehensive test suite
pytest tests/test_phase3.py -v
```

## Production Deployment

### 1. Environment Configuration

**Production .env:**
```bash
# Production environment variables
ENV=production

# Supabase (production project)
SUPABASE_URL=https://prod-project.supabase.co
SUPABASE_KEY=prod-anon-key

# Perplexity (production API key)
PERPLEXITY_API_KEY=pplx-prod-key

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/cambodia/app.log

# Performance tuning
EMBEDDING_BATCH_SIZE=32
MAX_WORKERS=4
```

### 2. Service Initialization (Singleton Pattern)

**Recommended: Initialize services once at startup**

```python
# app/main.py
from fastapi import FastAPI
from app.services.embedding_service import get_embedding_service
from app.services.semantic_search_service import SemanticSearchService
from app.services.supabase_service import SupabaseService
from app.config import settings

app = FastAPI()

# Global service instances (singleton)
_search_service = None
_perplexity_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global _search_service, _perplexity_service

    # Initialize embedding (loads model)
    embedding = get_embedding_service()

    # Initialize search
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
    _search_service = SemanticSearchService(supabase, embedding)

    # Initialize Perplexity
    from app.services.perplexity_service import PerplexityService
    _perplexity_service = PerplexityService(
        api_key=settings.perplexity_api_key,
        max_requests_per_month=1000
    )

    print("✅ All services initialized")

@app.get("/api/search")
async def search_endpoint(query: str, commodity: str = None):
    """Semantic search endpoint."""
    results = await _search_service.search(
        query=query,
        commodity=commodity,
        top_k=5
    )
    return {"results": results}

@app.post("/api/rag")
async def rag_endpoint(question: str, commodity: str):
    """RAG query endpoint."""
    # Get context
    context = await _search_service.search_with_context(
        query=question,
        commodity=commodity,
        top_k=5
    )

    # Generate answer
    result = await _perplexity_service.rag_query(
        query=question,
        retrieved_context=context,
        commodity=commodity
    )

    return {
        "answer": result['response_text'],
        "citations": result['citations'],
        "metadata": result['metadata']
    }
```

### 3. Monitoring and Logging

**Setup logging:**
```python
# app/logging_config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(log_file: str = "app.log"):
    """Setup application logging."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # File handler (rotating)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter('%(levelname)s - %(message)s')
    )
    logger.addHandler(console_handler)
```

**Monitor Perplexity usage:**
```python
# Add to dashboard or monitoring
from app.services.perplexity_service import PerplexityService

def get_perplexity_stats():
    stats = perplexity_service.get_stats()
    if stats['requests_remaining'] < 100:
        # Alert: low quota
        send_alert(f"Low Perplexity quota: {stats['requests_remaining']} remaining")
    return stats
```

### 4. Scaling Considerations

**Horizontal Scaling:**
- Embedding model: Load once per worker
- Supabase: Handles concurrent connections
- Perplexity: Shared rate limit across workers

**Vertical Scaling:**
- RAM: 8 GB per worker (for model)
- CPU: More cores = faster batch embedding
- GPU: 10-20x faster embeddings

**Caching:**
```python
# Cache frequent queries
from functools import lru_cache

@lru_cache(maxsize=1000)
async def cached_search(query: str, commodity: str):
    return await search_service.search(query, commodity=commodity)
```

## Maintenance

### Monthly Tasks

**1. Reset Perplexity Counter (1st of month)**
```bash
python -c "
from app.services.perplexity_service import PerplexityService
from app.config import settings

perplexity = PerplexityService(settings.perplexity_api_key)
perplexity.reset_counter()
print('✅ Perplexity counter reset')
"
```

**2. Add New Documents (as needed)**
```bash
# Chunk and embed new documents
python scripts/chunk_and_embed_new_documents.py
```

**3. Monitor Storage Usage**
```sql
-- Check database size
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename IN ('context_documents', 'document_embeddings')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Quarterly Tasks

**1. Reindex HNSW (if many inserts/deletes)**
```sql
-- Rebuild HNSW index
DROP INDEX idx_embedding_hnsw;
CREATE INDEX idx_embedding_hnsw
    ON document_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

**2. Vacuum Database**
```sql
-- Reclaim space and update statistics
VACUUM ANALYZE document_embeddings;
```

**3. Review Model Performance**
- Check search quality metrics
- Consider upgrading embedding model if needed
- Review chunk size/overlap settings

### Backup Strategy

**1. Database Backup (Supabase handles this)**
- Automatic daily backups (Pro plan)
- Point-in-time recovery

**2. Model Cache Backup**
```bash
# Backup Hugging Face cache
tar -czf model_cache_backup.tar.gz ~/.cache/huggingface/hub
```

**3. Code and Config Backup**
```bash
# Version control
git commit -am "Update configuration"
git push origin main
```

## Next Steps

- **Usage Guide**: See [USER_GUIDE.md](USER_GUIDE.md)
- **Performance Tuning**: See [PERFORMANCE.md](PERFORMANCE.md)
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **API Reference**: See [TECHNICAL_REFERENCE.md](TECHNICAL_REFERENCE.md)

---

**Need help? Refer to [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues.**
