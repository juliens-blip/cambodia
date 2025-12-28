# Troubleshooting Guide: Phase 3 Issues and Solutions

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Embedding Service Issues](#embedding-service-issues)
3. [Database Issues](#database-issues)
4. [Search Performance Issues](#search-performance-issues)
5. [RAG Query Issues](#rag-query-issues)
6. [API and Network Issues](#api-and-network-issues)
7. [Debugging Tools](#debugging-tools)

## Installation Issues

### Issue: Model Download Fails

**Symptoms:**
```
OSError: Can't load tokenizer for 'intfloat/multilingual-e5-large'
HTTPError: 403 Client Error: Forbidden for url: ...
```

**Causes:**
- Firewall blocking Hugging Face
- No internet connection
- Hugging Face API rate limit

**Solutions:**

1. **Check internet connection:**
   ```bash
   ping huggingface.co
   ```

2. **Use Hugging Face token (if rate limited):**
   ```python
   from huggingface_hub import login
   login(token="your-hf-token")  # Get from huggingface.co/settings/tokens

   embedding = EmbeddingService()
   ```

3. **Manual download:**
   ```bash
   # Download model manually
   git clone https://huggingface.co/intfloat/multilingual-e5-large

   # Load from local directory
   embedding = EmbeddingService(model_name="./multilingual-e5-large")
   ```

4. **Use mirror (China users):**
   ```python
   import os
   os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
   ```

---

### Issue: Insufficient Disk Space

**Symptoms:**
```
OSError: [Errno 28] No space left on device
```

**Cause:**
- Model cache requires ~2.2 GB
- Insufficient disk space

**Solutions:**

1. **Check disk space:**
   ```bash
   # Windows
   dir "C:\Users\<username>\.cache\huggingface"

   # Linux/Mac
   du -sh ~/.cache/huggingface
   ```

2. **Clear old models:**
   ```bash
   # List cached models
   ls ~/.cache/huggingface/hub

   # Remove unused models
   rm -rf ~/.cache/huggingface/hub/models--old-model-name
   ```

3. **Change cache location:**
   ```python
   import os
   os.environ['HF_HOME'] = '/path/to/large/disk'

   embedding = EmbeddingService()
   ```

---

### Issue: Dependencies Conflict

**Symptoms:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
ImportError: cannot import name 'SentenceTransformer' from 'sentence_transformers'
```

**Solutions:**

1. **Create fresh virtual environment:**
   ```bash
   # Remove old environment
   rm -rf .venv

   # Create new one
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate  # Windows

   # Install requirements
   pip install -r requirements.txt
   ```

2. **Update dependencies:**
   ```bash
   pip install --upgrade sentence-transformers torch transformers
   ```

3. **Check Python version:**
   ```bash
   python --version  # Should be 3.11+
   ```

---

## Embedding Service Issues

### Issue: Slow Embedding Generation

**Symptoms:**
- Single embedding takes >1 second
- Batch embedding very slow

**Causes:**
- Running on CPU (expected)
- Large batch size
- Inefficient usage pattern

**Solutions:**

1. **Use batch processing:**
   ```python
   # ❌ Slow
   embeddings = [embedding.embed_text(t) for t in texts]

   # ✅ Fast (10-20x speedup)
   embeddings = embedding.embed_batch(texts, batch_size=32)
   ```

2. **Install GPU support:**
   ```bash
   # Check if GPU available
   python -c "import torch; print(torch.cuda.is_available())"

   # Install CUDA version of PyTorch
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Optimize batch size:**
   ```python
   # CPU: smaller batches
   embeddings = embedding.embed_batch(texts, batch_size=16)

   # GPU: larger batches
   embeddings = embedding.embed_batch(texts, batch_size=64)
   ```

---

### Issue: Out of Memory (OOM)

**Symptoms:**
```
RuntimeError: CUDA out of memory
MemoryError: Unable to allocate array
```

**Causes:**
- Batch size too large for available RAM/VRAM
- Model + data doesn't fit in memory

**Solutions:**

1. **Reduce batch size:**
   ```python
   # Try smaller batches
   embeddings = embedding.embed_batch(texts, batch_size=8)  # Reduced from 32
   ```

2. **Process in chunks:**
   ```python
   # Split large dataset into smaller chunks
   def embed_large_dataset(texts, chunk_size=100):
       all_embeddings = []
       for i in range(0, len(texts), chunk_size):
           chunk = texts[i:i+chunk_size]
           embs = embedding.embed_batch(chunk, batch_size=16)
           all_embeddings.extend(embs)
       return all_embeddings
   ```

3. **Clear GPU cache (if using GPU):**
   ```python
   import torch
   torch.cuda.empty_cache()
   ```

---

### Issue: Embeddings Return NaN or Inf

**Symptoms:**
- Embeddings contain NaN or Inf values
- Search returns no results

**Causes:**
- Empty or malformed input text
- Encoding issues

**Solutions:**

1. **Validate input:**
   ```python
   def safe_embed(text: str):
       # Clean text
       text = text.strip()
       if not text:
           raise ValueError("Empty text")

       # Remove special characters
       text = ''.join(char for char in text if char.isprintable())

       return embedding.embed_text(text)
   ```

2. **Check for NaN:**
   ```python
   import numpy as np

   vec = embedding.embed_text("test")
   if np.isnan(vec).any() or np.isinf(vec).any():
       print("Warning: Invalid embedding!")
   ```

---

## Database Issues

### Issue: pgvector Extension Not Found

**Symptoms:**
```
ERROR: type "vector" does not exist
ERROR: operator does not exist: vector <=> vector
```

**Cause:**
- pgvector extension not enabled

**Solutions:**

1. **Enable extension in Supabase:**
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **Verify extension:**
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

3. **Check Supabase version:**
   - pgvector requires PostgreSQL 11+
   - Supabase projects created after 2022 should have it

---

### Issue: HNSW Index Build Fails

**Symptoms:**
```
ERROR: insufficient columns in HNSW index
ERROR: operator class "vector_cosine_ops" does not exist
```

**Solutions:**

1. **Create index AFTER data insertion:**
   ```sql
   -- ❌ Wrong: create index on empty table
   CREATE INDEX ... USING hnsw ...;
   INSERT INTO document_embeddings ...;

   -- ✅ Correct: insert data first
   INSERT INTO document_embeddings ...;
   CREATE INDEX ... USING hnsw ...;
   ```

2. **Check operator class:**
   ```sql
   -- Use correct operator class
   CREATE INDEX idx_embedding_hnsw
       ON document_embeddings
       USING hnsw (embedding vector_cosine_ops);  -- NOT vector_ops
   ```

3. **Rebuild index:**
   ```sql
   DROP INDEX IF EXISTS idx_embedding_hnsw;
   CREATE INDEX idx_embedding_hnsw
       ON document_embeddings
       USING hnsw (embedding vector_cosine_ops)
       WITH (m = 16, ef_construction = 64);
   ```

---

### Issue: Slow Search Without Index

**Symptoms:**
- Search takes 1-5 seconds
- Query plan shows sequential scan

**Cause:**
- HNSW index not created or not being used

**Solutions:**

1. **Check if index exists:**
   ```sql
   SELECT indexname, indexdef
   FROM pg_indexes
   WHERE tablename = 'document_embeddings';
   ```

2. **Force index usage:**
   ```sql
   SET enable_seqscan = OFF;  -- Disable sequential scans
   ```

3. **Verify query plan:**
   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM document_embeddings
   ORDER BY embedding <=> '[0,0,0,...]'::vector
   LIMIT 5;
   ```

   Should show: `Index Scan using idx_embedding_hnsw`

---

### Issue: Foreign Key Constraint Violation

**Symptoms:**
```
ERROR: insert or update on table "document_embeddings" violates foreign key constraint
DETAIL: Key (document_id)=(abc-123) is not present in table "context_documents"
```

**Cause:**
- Referenced document doesn't exist
- Document was deleted

**Solutions:**

1. **Verify document exists:**
   ```sql
   SELECT id FROM context_documents WHERE id = 'abc-123';
   ```

2. **Clean orphaned embeddings:**
   ```sql
   DELETE FROM document_embeddings
   WHERE document_id NOT IN (SELECT id FROM context_documents);
   ```

3. **Use ON DELETE CASCADE (already configured):**
   ```sql
   -- This should already be in schema
   ALTER TABLE document_embeddings
   ADD CONSTRAINT fk_document
   FOREIGN KEY (document_id)
   REFERENCES context_documents(id)
   ON DELETE CASCADE;
   ```

---

## Search Performance Issues

### Issue: Search Returns No Results

**Symptoms:**
- `search()` returns empty list
- No errors, just no matches

**Causes:**
1. No embeddings in database
2. Similarity threshold too high
3. Commodity filter too restrictive
4. Embedding dimension mismatch

**Solutions:**

1. **Check if embeddings exist:**
   ```python
   result = supabase.client.table('document_embeddings').select('id').limit(1).execute()
   print(f"Embeddings in DB: {len(result.data)}")
   ```

2. **Lower similarity threshold:**
   ```python
   # ❌ Too strict
   results = await search.search(query, similarity_threshold=0.9)

   # ✅ More permissive
   results = await search.search(query, similarity_threshold=0.6)
   ```

3. **Remove filters temporarily:**
   ```python
   # Test without filters
   results = await search.search(query)  # No commodity/source filter
   ```

4. **Check embedding dimension:**
   ```sql
   SELECT vector_dims(embedding) FROM document_embeddings LIMIT 1;
   -- Should return 1024
   ```

---

### Issue: Search Results Not Relevant

**Symptoms:**
- Search returns results, but they're off-topic
- Low similarity scores (<0.5)

**Causes:**
1. Query too vague
2. Documents don't contain relevant information
3. Wrong embedding model

**Solutions:**

1. **Make query more specific:**
   ```python
   # ❌ Vague
   results = await search.search("production")

   # ✅ Specific
   results = await search.search("cashew production statistics Kampong Thom 2024")
   ```

2. **Check what's in database:**
   ```python
   # Get sample documents
   result = supabase.client.table('document_embeddings').select('chunk_text').limit(5).execute()
   for chunk in result.data:
       print(chunk['chunk_text'][:200])
   ```

3. **Verify correct model:**
   ```python
   info = embedding.get_model_info()
   print(f"Model: {info['model_name']}")  # Should be multilingual-e5-large
   ```

---

### Issue: Inconsistent Search Results

**Symptoms:**
- Same query returns different results each time
- Results not deterministic

**Cause:**
- HNSW index is approximate (by design)

**Note:** This is EXPECTED behavior for HNSW indexes.

**Solutions:**

1. **Increase ef_search for more consistent results:**
   ```sql
   SET hnsw.ef_search = 200;  -- Default is 40
   ```

2. **Use higher similarity threshold:**
   ```python
   # Only return very confident matches
   results = await search.search(query, similarity_threshold=0.8)
   ```

3. **Accept approximate nature:** HNSW trades perfect accuracy for speed. If you need exact results, use brute-force:
   ```sql
   -- Exact (slow) search
   SELECT * FROM document_embeddings
   ORDER BY embedding <-> query_vector  -- Uses <-> instead of <=>
   LIMIT 5;
   ```

---

## RAG Query Issues

### Issue: Perplexity API Errors

**Symptoms:**
```
httpx.HTTPStatusError: 401 Client Error: Unauthorized
httpx.HTTPStatusError: 429 Too Many Requests
httpx.HTTPStatusError: 500 Internal Server Error
```

**Solutions:**

**401 Unauthorized:**
```python
# Check API key
print(f"API Key: {settings.perplexity_api_key[:10]}...")  # First 10 chars

# Verify key is valid
# Get new key from https://www.perplexity.ai/settings/api
```

**429 Too Many Requests:**
```python
# Check quota
stats = perplexity.get_stats()
print(f"Used: {stats['requests_used']}/{stats['rate_limit']}")

# Wait or upgrade plan
```

**500 Internal Server Error:**
```python
# Retry with exponential backoff
import asyncio

async def rag_with_retry(query, context, commodity, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await perplexity.rag_query(query, context, commodity)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 500 and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Retry {attempt+1}/{max_retries} after {wait_time}s")
                await asyncio.sleep(wait_time)
            else:
                raise
```

---

### Issue: RAG Response Doesn't Cite Local Documents

**Symptoms:**
- Perplexity returns generic answer
- No mention of local documents in response

**Causes:**
1. Context not included in prompt
2. Context not relevant enough
3. Perplexity model ignores context

**Solutions:**

1. **Verify context is being passed:**
   ```python
   context = await search.search_with_context(query, commodity="cashew")
   print(f"Context length: {len(context)} chars")
   print(f"Preview: {context[:200]}")

   # Should see formatted context with sources
   ```

2. **Increase top_k for more context:**
   ```python
   # More context = higher chance of relevant info
   context = await search.search_with_context(query, top_k=7)  # Instead of 5
   ```

3. **Check if local docs contain answer:**
   ```python
   # Manually review context
   if "relevant keyword" not in context.lower():
       print("Warning: Context may not contain answer!")
   ```

4. **Adjust prompt (in PerplexityService):**
   ```python
   # Make prompt more explicit
   prompt = f"""IMPORTANT: Base your answer PRIMARILY on the local documents below.
   Only use external knowledge to supplement.

   LOCAL DOCUMENTS:
   {retrieved_context}

   QUESTION: {query}
   """
   ```

---

### Issue: RAG Response Too Slow (>10 seconds)

**Symptoms:**
- RAG queries take very long
- Timeout errors

**Causes:**
1. Too much context (large token count)
2. Network latency
3. Perplexity API slow

**Solutions:**

1. **Reduce context size:**
   ```python
   # Smaller context = faster response
   context = await search.search_with_context(query, top_k=3)  # Instead of 5
   ```

2. **Increase timeout:**
   ```python
   # In PerplexityService._query()
   async with httpx.AsyncClient(timeout=120.0) as client:  # 2 minutes
       ...
   ```

3. **Monitor token usage:**
   ```python
   result = await perplexity.rag_query(query, context, commodity)
   tokens = result['metadata'].get('tokens_used', 0)
   if tokens > 5000:
       print(f"Warning: High token count ({tokens})")
   ```

---

## API and Network Issues

### Issue: Supabase Connection Timeout

**Symptoms:**
```
httpx.ConnectTimeout: timed out
supabase.lib.client_options.ClientOptionsError: Connection timeout
```

**Solutions:**

1. **Check internet connection:**
   ```bash
   ping your-project.supabase.co
   ```

2. **Verify credentials:**
   ```python
   print(f"Supabase URL: {settings.supabase_url}")
   print(f"Supabase Key: {settings.supabase_key[:20]}...")
   ```

3. **Increase timeout:**
   ```python
   from supabase import create_client

   supabase = create_client(
       settings.supabase_url,
       settings.supabase_key,
       options=ClientOptions(postgrest_client_timeout=30)  # 30 seconds
   )
   ```

---

### Issue: Supabase Row Level Security (RLS) Blocking Queries

**Symptoms:**
```
No rows returned even though data exists
SELECT works in SQL editor but not via API
```

**Cause:**
- RLS policies blocking access

**Solutions:**

1. **Check RLS policies:**
   ```sql
   SELECT * FROM pg_policies WHERE tablename = 'document_embeddings';
   ```

2. **Disable RLS for service role (if using service key):**
   ```sql
   ALTER TABLE document_embeddings DISABLE ROW LEVEL SECURITY;
   ```

3. **Or create permissive policy:**
   ```sql
   CREATE POLICY "Allow all access"
   ON document_embeddings
   FOR ALL
   USING (true);
   ```

---

## Debugging Tools

### 1. Embedding Inspection

```python
def inspect_embedding(text: str):
    """Debug embedding generation."""
    vec = embedding.embed_query(text)

    print(f"Text: {text}")
    print(f"Embedding dim: {len(vec)}")
    print(f"Embedding range: [{min(vec):.4f}, {max(vec):.4f}]")
    print(f"Embedding norm: {np.linalg.norm(vec):.4f}")
    print(f"Sample values: {vec[:5]}")

    # Check for issues
    if np.isnan(vec).any():
        print("WARNING: NaN values detected!")
    if np.isinf(vec).any():
        print("WARNING: Inf values detected!")
    if all(v == 0 for v in vec):
        print("WARNING: All zeros!")

inspect_embedding("Test query")
```

### 2. Search Debugging

```python
async def debug_search(query: str):
    """Debug semantic search."""
    print(f"\n{'='*60}")
    print(f"SEARCH DEBUG: {query}")
    print(f"{'='*60}")

    # Step 1: Generate embedding
    print("\n1. Embedding generation...")
    query_vec = embedding.embed_query(query)
    print(f"   Dimension: {len(query_vec)}")
    print(f"   Norm: {np.linalg.norm(query_vec):.4f}")

    # Step 2: Database query
    print("\n2. Database query...")
    results = await search.search(query, top_k=5, similarity_threshold=0.0)
    print(f"   Results: {len(results)}")

    # Step 3: Result analysis
    print("\n3. Results:")
    for i, result in enumerate(results[:3], 1):
        print(f"   [{i}] Similarity: {result['similarity']:.4f}")
        print(f"       Source: {result['metadata']['source']}")
        print(f"       Text: {result['chunk_text'][:100]}...")

    print(f"\n{'='*60}\n")

await debug_search("cashew production")
```

### 3. Database Inspection

```python
async def inspect_database():
    """Inspect database state."""
    print("DATABASE INSPECTION")
    print("="*60)

    # Count embeddings
    result = supabase.client.table('document_embeddings').select('id', count='exact').execute()
    print(f"Total chunks: {result.count}")

    # Check dimensions
    result = supabase.client.rpc('get_embedding_stats').execute()
    # Or manually:
    result = supabase.client.table('document_embeddings').select('embedding').limit(1).execute()
    if result.data:
        dim = len(result.data[0]['embedding'])
        print(f"Embedding dimension: {dim}")

    # Sample chunks
    result = supabase.client.table('document_embeddings').select('chunk_text, metadata').limit(3).execute()
    print("\nSample chunks:")
    for i, chunk in enumerate(result.data, 1):
        print(f"  [{i}] {chunk['metadata'].get('title', 'Untitled')}")
        print(f"      {chunk['chunk_text'][:100]}...")

    print("="*60)

await inspect_database()
```

### 4. Logging Configuration

```python
import logging

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,  # Show all logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Component-specific logging
logging.getLogger('app.services.embedding_service').setLevel(logging.DEBUG)
logging.getLogger('app.services.semantic_search_service').setLevel(logging.DEBUG)
logging.getLogger('httpx').setLevel(logging.WARNING)  # Reduce httpx noise
```

### 5. Performance Profiling

```python
import cProfile
import pstats

async def profile_search():
    """Profile search performance."""
    profiler = cProfile.Profile()
    profiler.enable()

    # Run search
    results = await search.search("cashew production", top_k=5)

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 slowest functions

asyncio.run(profile_search())
```

---

## Common Error Messages

### Quick Reference

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| `ModuleNotFoundError: No module named 'sentence_transformers'` | Missing dependency | `pip install sentence-transformers` |
| `CUDA out of memory` | Batch size too large | Reduce batch_size |
| `type "vector" does not exist` | pgvector not enabled | `CREATE EXTENSION vector;` |
| `401 Unauthorized` (Perplexity) | Invalid API key | Check PERPLEXITY_API_KEY |
| `429 Too Many Requests` | Rate limit exceeded | Wait or upgrade plan |
| `No results found` | Threshold too high | Lower similarity_threshold |
| `Connection timeout` | Network issue | Check internet, increase timeout |

---

## Getting Help

If issues persist:

1. **Check logs:** Enable DEBUG logging and review error messages
2. **Verify setup:** Run through [SETUP_GUIDE.md](SETUP_GUIDE.md) again
3. **Test components:** Use debugging tools above to isolate problem
4. **Review docs:** Check [TECHNICAL_REFERENCE.md](TECHNICAL_REFERENCE.md) for API details
5. **Search issues:** Look for similar errors in GitHub issues
6. **Ask for help:** Provide logs, error messages, and steps to reproduce

---

**For performance issues, see [PERFORMANCE.md](PERFORMANCE.md).**
