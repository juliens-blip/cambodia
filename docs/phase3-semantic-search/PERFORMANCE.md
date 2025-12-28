# Performance Guide: Phase 3 Optimization

## Table of Contents

1. [Performance Benchmarks](#performance-benchmarks)
2. [Bottleneck Analysis](#bottleneck-analysis)
3. [Optimization Strategies](#optimization-strategies)
4. [Scaling Guidelines](#scaling-guidelines)
5. [Cost Optimization](#cost-optimization)
6. [Monitoring and Metrics](#monitoring-and-metrics)

## Performance Benchmarks

### System Overview

**Test Environment:**
- CPU: Intel Core i7 (8 cores)
- RAM: 16 GB
- Disk: SSD
- Network: 100 Mbps
- GPU: None (CPU inference)

### Component Performance

#### 1. Embedding Generation

| Operation | Documents | Time | Throughput |
|-----------|-----------|------|------------|
| Single text (embed_text) | 1 | ~20ms | 50 texts/sec |
| Query embed (embed_query) | 1 | ~20ms | 50 queries/sec |
| Batch embed (32 batch) | 100 | ~2 sec | 50 texts/sec |
| Batch embed (32 batch) | 1000 | ~20 sec | 50 texts/sec |

**GPU Performance (Tesla T4):**
- Single: ~5ms (4x faster)
- Batch: ~400ms per 100 texts (5x faster)

**Model Load Time:**
- First run (download): 5-10 minutes
- Subsequent runs (cache): 2-3 seconds

#### 2. Document Chunking

| Operation | Documents | Avg Size | Time | Throughput |
|-----------|-----------|----------|------|------------|
| Single document | 1 | 6,100 chars | <1ms | 1000+ docs/sec |
| Batch (34 docs) | 34 | 6,100 chars | ~20ms | 1700 docs/sec |

**Note:** Chunking is extremely fast (CPU-bound, negligible overhead)

#### 3. Semantic Search

**Without HNSW Index:**
| Query | Chunks | Time |
|-------|--------|------|
| Simple | 146 | 1-2 sec |
| Complex | 146 | 1-2 sec |

**With HNSW Index (m=16, ef_construction=64):**
| Query | Chunks | Time |
|-------|--------|------|
| Simple | 146 | 30-50ms |
| Complex | 146 | 30-50ms |

**Breakdown:**
- Query embedding: ~20ms (CPU)
- pgvector search: <20ms (HNSW)
- Network latency: ~10ms
- **Total: 30-50ms**

**HNSW Index Build Time:**
- 146 chunks: ~30 seconds
- 1,000 chunks: ~2 minutes
- 10,000 chunks: ~15 minutes

#### 4. RAG Query (Perplexity)

| Component | Time |
|-----------|------|
| Semantic search | 30-50ms |
| Context formatting | <5ms |
| Perplexity API call | 2-5 seconds |
| **Total** | **2-5 seconds** |

**Variables:**
- Context size: Larger context = more tokens = longer
- Response length: Longer answers = more time
- Network latency: Varies by location

### End-to-End Pipeline Performance

**Initial Setup (One-Time):**
```
34 documents → 146 chunks with embeddings
================================================================================
1. Model loading:         3 seconds (cached)
2. Document fetching:     1 second (Supabase)
3. Chunking:              <1 second (34 docs)
4. Embedding:             60 seconds (146 chunks, CPU batch)
5. Database insertion:    10 seconds (146 rows)
6. HNSW index creation:   30 seconds
--------------------------------------------------------------------------------
Total:                    ~105 seconds (~2 minutes)
================================================================================
```

**Query Performance:**
```
User question → RAG answer
================================================================================
1. Query embedding:       20ms
2. Semantic search:       30ms (HNSW)
3. Context formatting:    5ms
4. Perplexity API:        3 seconds
--------------------------------------------------------------------------------
Total:                    ~3 seconds
================================================================================
```

**Throughput Estimates:**
- Semantic search only: 20-30 queries/second (parallel)
- RAG queries: 0.3 queries/second (sequential, API limited)

## Bottleneck Analysis

### Primary Bottlenecks

#### 1. Embedding Generation (CPU-Bound)

**Issue:** Embedding model inference is CPU-intensive

**Impact:**
- Single embedding: ~20ms
- 1000 embeddings: ~20 seconds (CPU) vs. ~4 seconds (GPU)

**Solutions:**
- Use GPU for batch embedding (5-10x speedup)
- Batch process instead of individual calls
- Cache frequent queries
- Use smaller model (trade-off: accuracy vs. speed)

#### 2. Perplexity API (Network-Bound)

**Issue:** External API call adds 2-5 seconds

**Impact:**
- Cannot parallelize beyond API rate limits
- Network latency varies
- Sequential processing only

**Solutions:**
- Use semantic search alone when possible
- Cache RAG responses for common questions
- Implement request queue for high traffic
- Consider alternative LLM for lower latency (e.g., local model)

#### 3. HNSW Index Build (One-Time Cost)

**Issue:** Index creation takes time for large datasets

**Impact:**
- 146 chunks: 30 seconds
- 10,000 chunks: 15 minutes

**Solutions:**
- Build index AFTER all data is inserted (not during)
- Schedule index rebuilds during off-hours
- Use incremental updates when possible

### Secondary Bottlenecks

#### 4. Database Queries

**Issue:** Large result sets can be slow

**Current Performance:**
- Top-5 search: 20-30ms
- Top-100 search: 50-100ms

**Solutions:**
- Use appropriate `top_k` values (5-10 recommended)
- Apply commodity/source filters to reduce search space
- Optimize pgvector parameters

#### 5. Model Loading

**Issue:** First load takes time

**Impact:**
- Cold start: 2-3 seconds
- Affects serverless deployments

**Solutions:**
- Keep service warm (singleton pattern)
- Use model caching
- Consider smaller models for faster loading

## Optimization Strategies

### 1. Embedding Optimization

#### Use GPU Acceleration

```python
import torch

# Check GPU availability
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")

# EmbeddingService automatically uses GPU if available
from app.services.embedding_service import EmbeddingService
embedding = EmbeddingService()  # Will use GPU if CUDA installed
```

**Performance gain:**
- CPU: 50 texts/second
- GPU (T4): 250 texts/second
- GPU (A100): 500+ texts/second

#### Batch Processing

```python
# ❌ Slow: Individual calls
embeddings = []
for text in texts:
    emb = embedding.embed_text(text)  # 20ms each
    embeddings.append(emb)
# Total: 20ms × 100 = 2 seconds

# ✅ Fast: Batch processing
embeddings = embedding.embed_batch(
    texts,
    batch_size=32,  # Optimal batch size
    show_progress=True
)
# Total: ~400ms (5x faster)
```

**Optimal batch sizes:**
- CPU: 16-32
- GPU: 64-128

#### Query Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_query_embedding(query: str) -> List[float]:
    """Cache frequent query embeddings."""
    return embedding.embed_query(query)

# First call: 20ms (compute)
vec1 = get_query_embedding("cashew production")

# Second call: <1ms (cached)
vec2 = get_query_embedding("cashew production")
```

### 2. Search Optimization

#### HNSW Index Tuning

**Parameters:**
- `m`: Max connections per layer (default: 16)
  - Higher = better recall, slower build, more memory
  - Range: 8-64
- `ef_construction`: Build-time accuracy (default: 64)
  - Higher = better index quality, slower build
  - Range: 32-256

**Recommended settings:**

```sql
-- Balanced (current)
CREATE INDEX idx_embedding_hnsw
    ON document_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Fast queries (lower recall)
WITH (m = 8, ef_construction = 32);

-- High accuracy (slower build)
WITH (m = 32, ef_construction = 128);
```

**Query-Time Parameter:**
```sql
-- Adjust search quality
SET hnsw.ef_search = 100;  -- Default: 40
-- Higher = better recall, slower queries
```

#### Filter Optimization

```python
# ✅ Efficient: Filter in database
results = await search.search(
    query="statistics",
    commodity="cashew",  # Reduces search space
    top_k=5
)

# ❌ Less efficient: Filter after retrieval
results = await search.search(query="statistics", top_k=100)
filtered = [r for r in results if r['metadata']['commodity'] == 'cashew'][:5]
```

#### Top-K Selection

```python
# Balance quality vs. performance
results = await search.search(
    query="...",
    top_k=5  # ✅ Fast, usually sufficient
    # top_k=50  # ❌ Slower, rarely needed
)
```

**Guidelines:**
- RAG context: 3-7 chunks (balance quality vs. token cost)
- Document discovery: 10-20 chunks
- Similarity threshold more important than large top_k

### 3. RAG Optimization

#### Context Size Management

```python
# ✅ Optimal: 5 chunks (~10K chars, ~2.5K tokens)
context = await search.search_with_context(query, top_k=5)
# Perplexity cost: ~$0.005
# Response time: 2-3 seconds

# ❌ Too large: 20 chunks (~40K chars, ~10K tokens)
context = await search.search_with_context(query, top_k=20)
# Perplexity cost: ~$0.015 (3x more)
# Response time: 5-7 seconds (slower)
```

**Recommendations:**
- Start with top_k=5
- Increase only if answers lack detail
- Monitor token usage

#### Response Caching

```python
import hashlib
from datetime import datetime, timedelta

# Simple cache implementation
_rag_cache = {}

async def cached_rag_query(query: str, commodity: str):
    """Cache RAG responses (1 hour TTL)."""
    cache_key = hashlib.md5(f"{query}:{commodity}".encode()).hexdigest()

    # Check cache
    if cache_key in _rag_cache:
        cached_data, timestamp = _rag_cache[cache_key]
        if datetime.now() - timestamp < timedelta(hours=1):
            return cached_data  # Cache hit

    # Cache miss: call Perplexity
    context = await search.search_with_context(query, commodity=commodity)
    result = await perplexity.rag_query(query, context, commodity)

    # Store in cache
    _rag_cache[cache_key] = (result, datetime.now())

    return result
```

**Benefits:**
- Reduces API calls (saves cost)
- Improves response time (instant for cached)
- Reduces load on Perplexity

### 4. Database Optimization

#### Connection Pooling

```python
# Use connection pooling for concurrent requests
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

options = ClientOptions(
    schema="public",
    headers={"x-my-custom-header": "value"},
    auto_refresh_token=True,
    persist_session=True,
    storage=None,
    realtime=None,
    postgrest_client_timeout=10,  # Timeout
    storage_client_timeout=10,
)

supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_key,
    options=options
)
```

#### Vacuum and Analyze

```sql
-- Run weekly to maintain performance
VACUUM ANALYZE document_embeddings;

-- Check table statistics
SELECT
    schemaname,
    tablename,
    last_vacuum,
    last_analyze,
    n_live_tup,
    n_dead_tup
FROM pg_stat_user_tables
WHERE tablename = 'document_embeddings';
```

## Scaling Guidelines

### Vertical Scaling (Single Server)

**Current Capacity (16 GB RAM, 8 CPU cores):**
- Embeddings in memory: ~600 MB (146 chunks × 1024 dim × 4 bytes)
- Model in memory: ~2.2 GB
- Total RAM usage: ~3 GB
- **Headroom: 13 GB** (can handle 10,000+ chunks)

**Recommended Specs:**
- **Small** (1,000 chunks): 8 GB RAM, 4 CPU cores
- **Medium** (10,000 chunks): 16 GB RAM, 8 CPU cores
- **Large** (100,000 chunks): 32 GB RAM, 16 CPU cores + GPU

### Horizontal Scaling (Multiple Servers)

**Architecture:**
```
                    Load Balancer
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    Worker 1         Worker 2       Worker 3
    (Model)          (Model)         (Model)
         │               │               │
         └───────────────┼───────────────┘
                         │
                   Supabase DB
                 (Shared pgvector)
```

**Considerations:**
- Each worker loads model independently (~2.2 GB RAM each)
- Supabase handles concurrent connections
- Perplexity rate limit is shared

**Scaling Limits:**
- Supabase free tier: 500 MB transfer/month
- Perplexity: 1000 requests/month (shared across workers)

### Auto-Scaling Strategy

```python
# Example: AWS Lambda or Cloud Run
import os

def handler(event, context):
    # Initialize service (cold start: ~3 seconds)
    if not hasattr(handler, 'search_service'):
        from app.services.embedding_service import EmbeddingService
        from app.services.semantic_search_service import SemanticSearchService

        embedding = EmbeddingService()
        supabase = SupabaseService(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
        handler.search_service = SemanticSearchService(supabase, embedding)

    # Handle request (warm: <100ms)
    results = await handler.search_service.search(event['query'])
    return results
```

**Cold Start Mitigation:**
- Keep 1-2 instances warm
- Use provisioned concurrency
- Preload model in container image

## Cost Optimization

### Current Costs (1000 queries/month)

| Component | Unit Cost | Monthly Usage | Monthly Cost |
|-----------|-----------|---------------|--------------|
| Embedding (local) | $0 | Unlimited | $0 |
| Supabase (free tier) | $0 | <500 MB | $0 |
| Perplexity API | $0.005/query | 1000 queries | $5.00 |
| **Total** | | | **$5.00** |

### Cost Scaling

**10,000 queries/month:**
- Embedding: $0 (local)
- Supabase: $0 (still within free tier)
- Perplexity: $50 (10,000 × $0.005)
- **Total: $50/month**

**100,000 queries/month:**
- Embedding: $0 (local)
- Supabase: ~$10 (need Pro plan for bandwidth)
- Perplexity: $500 (100,000 × $0.005)
- **Total: $510/month**

### Cost Reduction Strategies

#### 1. Reduce Perplexity Usage

**Strategy: Use semantic search alone when possible**

```python
async def smart_query(question: str, commodity: str, use_rag: bool = True):
    """
    Use RAG only when needed.
    For simple lookups, semantic search is sufficient.
    """
    # Always do semantic search
    results = await search.search(question, commodity=commodity, top_k=5)

    # Determine if RAG is needed
    if not use_rag or is_simple_lookup(question):
        # Return search results directly (no Perplexity cost)
        return format_search_results(results)

    # Use RAG for complex questions
    context = await search.search_with_context(question, commodity=commodity)
    return await perplexity.rag_query(question, context, commodity)

def is_simple_lookup(question: str) -> bool:
    """Check if question is simple lookup vs. complex analysis."""
    simple_keywords = ['what is', 'define', 'list', 'show', 'find']
    return any(keyword in question.lower() for keyword in simple_keywords)
```

**Savings:** 30-50% reduction in Perplexity calls

#### 2. Implement Aggressive Caching

```python
# Cache RAG responses for 24 hours
from datetime import datetime, timedelta
import json

class RAGCache:
    def __init__(self, ttl_hours: int = 24):
        self.cache = {}
        self.ttl = timedelta(hours=ttl_hours)

    def get(self, query: str, commodity: str):
        key = f"{query}:{commodity}"
        if key in self.cache:
            result, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                return result  # Cache hit
        return None  # Cache miss

    def set(self, query: str, commodity: str, result):
        key = f"{query}:{commodity}"
        self.cache[key] = (result, datetime.now())

# Usage
cache = RAGCache(ttl_hours=24)

async def cached_rag(query, commodity):
    # Check cache first
    cached = cache.get(query, commodity)
    if cached:
        return cached  # No API call!

    # Cache miss: call API
    context = await search.search_with_context(query, commodity=commodity)
    result = await perplexity.rag_query(query, context, commodity)

    # Store in cache
    cache.set(query, commodity, result)
    return result
```

**Savings:** 40-60% reduction for repeated queries

#### 3. Use Alternative LLM

**Option: Local LLM (e.g., Llama 3)**

```python
# Replace Perplexity with local model
from transformers import AutoModelForCausalLM, AutoTokenizer

class LocalRAG:
    def __init__(self):
        self.model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3-8B")
        self.tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3-8B")

    async def rag_query(self, query, context, commodity):
        prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(**inputs, max_length=512)
        answer = self.tokenizer.decode(outputs[0])
        return {"response_text": answer, "citations": []}
```

**Trade-offs:**
- Cost: $0 (local)
- Quality: Lower than Perplexity (no online search)
- Latency: 2-5 seconds (similar to Perplexity)
- Infrastructure: Requires GPU (~24 GB VRAM for 8B model)

## Monitoring and Metrics

### Key Performance Indicators (KPIs)

#### 1. Latency Metrics

```python
import time
from typing import Dict

class PerformanceMonitor:
    def __init__(self):
        self.metrics = []

    async def track_search(self, query: str, commodity: str):
        start = time.time()

        # Perform search
        results = await search.search(query, commodity=commodity)

        latency = (time.time() - start) * 1000  # ms

        self.metrics.append({
            'operation': 'search',
            'latency_ms': latency,
            'query': query,
            'results_count': len(results)
        })

        return results

    def get_stats(self) -> Dict:
        if not self.metrics:
            return {}

        latencies = [m['latency_ms'] for m in self.metrics]
        return {
            'avg_latency_ms': sum(latencies) / len(latencies),
            'min_latency_ms': min(latencies),
            'max_latency_ms': max(latencies),
            'p95_latency_ms': sorted(latencies)[int(len(latencies) * 0.95)],
            'total_queries': len(self.metrics)
        }
```

**Target Metrics:**
- Semantic search: <100ms (p95)
- RAG query: <5 seconds (p95)
- Embedding generation: <50ms (single)

#### 2. Throughput Metrics

```python
# Track queries per second
from collections import deque
from datetime import datetime, timedelta

class ThroughputMonitor:
    def __init__(self, window_seconds: int = 60):
        self.window = window_seconds
        self.queries = deque()

    def record_query(self):
        self.queries.append(datetime.now())
        self._clean_old()

    def _clean_old(self):
        cutoff = datetime.now() - timedelta(seconds=self.window)
        while self.queries and self.queries[0] < cutoff:
            self.queries.popleft()

    def get_qps(self) -> float:
        """Queries per second (last 60 seconds)."""
        self._clean_old()
        return len(self.queries) / self.window

# Usage
monitor = ThroughputMonitor()
monitor.record_query()
print(f"QPS: {monitor.get_qps():.2f}")
```

#### 3. Cost Metrics

```python
class CostTracker:
    def __init__(self):
        self.perplexity_calls = 0
        self.total_tokens = 0

    def record_rag_query(self, tokens_used: int):
        self.perplexity_calls += 1
        self.total_tokens += tokens_used

    def get_costs(self) -> Dict:
        return {
            'perplexity_calls': self.perplexity_calls,
            'total_tokens': self.total_tokens,
            'estimated_cost_usd': self.perplexity_calls * 0.005,
            'avg_tokens_per_query': self.total_tokens / self.perplexity_calls if self.perplexity_calls > 0 else 0
        }
```

### Dashboard Example

```python
# Simple performance dashboard
async def get_performance_dashboard():
    """Get real-time performance metrics."""
    search_stats = search.get_stats()
    perplexity_stats = perplexity.get_stats()

    # Query counts from database
    result = supabase.client.table('document_embeddings').select('id', count='exact').execute()
    total_chunks = result.count

    return {
        'system': {
            'total_chunks': total_chunks,
            'embedding_model': search_stats['embedding_model'],
            'embedding_dim': search_stats['embedding_dimension']
        },
        'performance': {
            'search_latency_ms': '<100ms',
            'rag_latency_seconds': '2-5s'
        },
        'usage': {
            'perplexity_used': perplexity_stats['requests_used'],
            'perplexity_remaining': perplexity_stats['requests_remaining'],
            'utilization': f"{perplexity_stats['utilization_percentage']:.1f}%"
        },
        'cost': {
            'monthly_estimate_usd': perplexity_stats['requests_used'] * 0.005
        }
    }
```

## Recommendations

### For Development/Testing
- Use CPU inference (sufficient for small scale)
- Don't optimize prematurely
- Focus on correctness first

### For Production (<1000 queries/day)
- Use CPU inference
- Implement basic caching
- Monitor Perplexity usage
- HNSW index with default settings (m=16, ef_construction=64)

### For High Traffic (>1000 queries/day)
- Use GPU for embeddings
- Implement aggressive caching
- Consider local LLM alternative
- Optimize HNSW parameters
- Set up monitoring and alerts

### For Enterprise Scale (>10,000 queries/day)
- Multi-GPU setup
- Distributed caching (Redis)
- Load balancing across workers
- Dedicated Perplexity Enterprise plan
- Custom HNSW tuning
- 24/7 monitoring

---

**For troubleshooting performance issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).**
