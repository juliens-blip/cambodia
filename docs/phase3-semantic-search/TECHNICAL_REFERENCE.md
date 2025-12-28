# Technical Reference: Phase 3 API Documentation

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [EmbeddingService](#embeddingservice)
3. [ChunkingService](#chunkingservice)
4. [SemanticSearchService](#semanticsearchservice)
5. [PerplexityService](#perplexityservice)
6. [Database Schema](#database-schema)
7. [Integration Guide](#integration-guide)

## Architecture Overview

### System Components

```
┌────────────────────────────────────────────────────────────┐
│                     Application Layer                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────┐       ┌──────────────────┐          │
│  │ Semantic Search  │       │  Perplexity      │          │
│  │    Service       │◄──────┤  RAG Service     │          │
│  └────────┬─────────┘       └──────────────────┘          │
│           │                                                │
│           ▼                                                │
│  ┌──────────────────┐       ┌──────────────────┐          │
│  │   Embedding      │       │   Chunking       │          │
│  │    Service       │       │   Service        │          │
│  └────────┬─────────┘       └──────────────────┘          │
│           │                                                │
├───────────┼────────────────────────────────────────────────┤
│           │         Infrastructure Layer                   │
│           ▼                                                │
│  ┌──────────────────┐       ┌──────────────────┐          │
│  │    Supabase      │       │  Hugging Face    │          │
│  │    pgvector      │       │  Transformers    │          │
│  └──────────────────┘       └──────────────────┘          │
└────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Document Ingestion** (one-time)
   ```
   Raw Documents → ChunkingService → Chunks → EmbeddingService → Vectors → Supabase
   ```

2. **Semantic Search**
   ```
   Query → EmbeddingService → Query Vector → SemanticSearchService → Top-K Chunks
   ```

3. **RAG Query**
   ```
   Question → SemanticSearch → Context → PerplexityService → AI Answer
   ```

## EmbeddingService

**Location**: `app/services/embedding_service.py`

**Purpose**: Generate multilingual embeddings using the `multilingual-e5-large` model.

### Class: `EmbeddingService`

#### Constructor

```python
def __init__(self, model_name: str = "intfloat/multilingual-e5-large")
```

**Parameters:**
- `model_name` (str): Hugging Face model identifier
  - Default: `"intfloat/multilingual-e5-large"`
  - Dimension: 1024
  - Languages: 100+

**Behavior:**
- Downloads model to cache on first run (~2.2 GB)
- Subsequent runs load from cache (fast)
- Uses CPU by default (GPU if available via PyTorch)

**Example:**
```python
from app.services.embedding_service import EmbeddingService

# Initialize (downloads model on first run)
embedding = EmbeddingService()

# Or use different model
embedding = EmbeddingService(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
```

---

#### Method: `embed_text(text: str) -> List[float]`

Generate embedding for a document passage (for storage).

**Parameters:**
- `text` (str): Text to embed

**Returns:**
- `List[float]`: Embedding vector (1024 dimensions)

**Implementation Details:**
- Automatically prefixes text with `"passage: "` (E5 model requirement)
- Uses `model.encode()` with numpy conversion

**Example:**
```python
# Embed document text
vector = embedding.embed_text("Cashew production in Cambodia increased by 15%")

# Check dimension
print(len(vector))  # 1024

# Vector is list of floats
print(type(vector))  # <class 'list'>
print(type(vector[0]))  # <class 'float'>
```

---

#### Method: `embed_query(query: str) -> List[float]`

Generate embedding for a search query (for retrieval).

**Parameters:**
- `query` (str): Query text

**Returns:**
- `List[float]`: Embedding vector (1024 dimensions)

**Implementation Details:**
- Automatically prefixes text with `"query: "` (E5 model requirement)
- Different prefix than `embed_text()` for optimal retrieval performance

**Example:**
```python
# Embed search query
query_vector = embedding.embed_query("ការផលិតស្វាយចន្ទី")  # Khmer

# Use for similarity search
results = await search.search(query="...", query_vector=query_vector)
```

**Why Different Prefixes?**

E5 models use asymmetric embedding:
- **Queries**: Short, question-like (`"query: "` prefix)
- **Passages**: Longer, informational (`"passage: "` prefix)

This improves cross-lingual retrieval accuracy.

---

#### Method: `embed_batch(texts: List[str], batch_size: int = 32, show_progress: bool = True) -> List[List[float]]`

Generate embeddings for multiple texts efficiently.

**Parameters:**
- `texts` (List[str]): List of texts to embed
- `batch_size` (int, optional): Batch size for processing (default: 32)
- `show_progress` (bool, optional): Show progress bar (default: True)

**Returns:**
- `List[List[float]]`: List of embedding vectors

**Performance:**
- **CPU**: ~50-100 texts/second
- **GPU**: ~500-1000 texts/second
- Batching is **10-20x faster** than individual calls

**Example:**
```python
# Embed 100 documents
texts = [doc['text_content'] for doc in documents]

embeddings = embedding.embed_batch(
    texts,
    batch_size=32,  # Process 32 at a time
    show_progress=True  # Show progress bar
)

# Result
print(len(embeddings))  # 100
print(len(embeddings[0]))  # 1024
```

---

#### Method: `cosine_similarity(embedding1, embedding2) -> float`

Calculate cosine similarity between two embeddings.

**Parameters:**
- `embedding1` (List[float] | np.ndarray): First embedding
- `embedding2` (List[float] | np.ndarray): Second embedding

**Returns:**
- `float`: Similarity score (0.0 to 1.0)
  - 1.0 = identical
  - 0.0 = orthogonal (unrelated)
  - <0.0 = opposite (rare)

**Formula:**
```
similarity = dot(v1, v2) / (norm(v1) * norm(v2))
```

**Example:**
```python
# Compare embeddings
vec1 = embedding.embed_query("cashew")
vec2 = embedding.embed_query("ស្វាយចន្ទី")  # Khmer: cashew

similarity = embedding.cosine_similarity(vec1, vec2)
print(f"Similarity: {similarity:.4f}")  # e.g., 0.8315 (high)
```

**Note**: Supabase pgvector uses cosine **distance** (1 - similarity):
- pgvector distance 0.2 = similarity 0.8
- pgvector distance 0.0 = similarity 1.0

---

#### Method: `get_model_info() -> dict`

Get model metadata and configuration.

**Returns:**
- `dict`: Model information

**Example:**
```python
info = embedding.get_model_info()
print(info)
# {
#     'model_name': 'intfloat/multilingual-e5-large',
#     'dimension': 1024,
#     'max_seq_length': 512,
#     'languages': '100+ (including Khmer, English, Vietnamese)',
#     'cost': '$0 (local inference)',
#     'prefix_query': 'query: ',
#     'prefix_passage': 'passage: '
# }
```

---

#### Function: `get_embedding_service() -> EmbeddingService`

Get singleton embedding service instance (module-level).

**Returns:**
- `EmbeddingService`: Singleton instance

**Use Case:** Avoid loading model multiple times

**Example:**
```python
from app.services.embedding_service import get_embedding_service

# First call: loads model
service1 = get_embedding_service()

# Second call: reuses same instance (no reload)
service2 = get_embedding_service()

assert service1 is service2  # True (same object)
```

---

## ChunkingService

**Location**: `app/services/chunking_service.py`

**Purpose**: Split documents into chunks using recursive character text splitting.

### Class: `ChunkingService`

#### Constructor

```python
def __init__(
    self,
    chunk_size: int = 2048,
    chunk_overlap: int = 200,
    separators: Optional[List[str]] = None
)
```

**Parameters:**
- `chunk_size` (int): Target chunk size in characters (default: 2048)
  - ~512 tokens (optimal for multilingual-e5-large)
- `chunk_overlap` (int): Character overlap between chunks (default: 200)
  - ~10% overlap prevents context loss at boundaries
- `separators` (List[str], optional): Split separators (default: `["\n\n", "\n", " ", ""]`)

**Strategy:**
1. Try splitting by paragraphs (`\n\n`)
2. If too large, split by lines (`\n`)
3. If still too large, split by words (` `)
4. Last resort: split by characters (`""`)

**Example:**
```python
from app.services.chunking_service import ChunkingService

# Default configuration (recommended)
chunking = ChunkingService()

# Custom configuration
chunking = ChunkingService(
    chunk_size=1024,  # Smaller chunks
    chunk_overlap=100,  # Less overlap
    separators=["\n\n", "\n", ". ", " ", ""]  # Add sentence splitting
)
```

---

#### Method: `chunk_document(text: str, document_id: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]`

Chunk a single document into smaller pieces.

**Parameters:**
- `text` (str): Document text content
- `document_id` (str): UUID of source document
- `metadata` (dict, optional): Additional metadata to attach to each chunk

**Returns:**
- `List[Dict[str, Any]]`: List of chunk dictionaries

**Chunk Structure:**
```python
{
    'document_id': 'abc-123-uuid',
    'chunk_index': 0,  # 0-based index
    'chunk_text': 'Actual chunk text content...',
    'metadata': {
        # Original metadata
        'source': 'GDrive',
        'commodity': 'cashew',
        'title': 'iTrade Bulletin Q2 2024',
        # Added by chunking service
        'chunk_index': 0,
        'total_chunks': 5,
        'char_count': 2048,
        'has_overlap': False  # True for chunks after first
    }
}
```

**Example:**
```python
# Chunk single document
text = "Long document text..." * 100  # ~2000 chars
chunks = chunking.chunk_document(
    text,
    document_id="abc-123",
    metadata={
        'source': 'GDrive',
        'commodity': 'cashew',
        'title': 'Market Report'
    }
)

print(f"Created {len(chunks)} chunks")
for chunk in chunks:
    print(f"  Chunk {chunk['chunk_index']}: {len(chunk['chunk_text'])} chars")
```

---

#### Method: `chunk_documents_batch(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]`

Chunk multiple documents in batch.

**Parameters:**
- `documents` (List[dict]): List of document dicts

**Document Structure:**
```python
{
    'id': 'uuid',
    'text_content': 'Document text...',
    'source': 'GDrive',
    'commodity': 'cashew',
    'title': 'Report Title',
    'url': 'https://...',
    'extraction_method': 'PyPDF2',
    'scraped_at': '2024-12-26T10:00:00'
}
```

**Returns:**
- `List[Dict[str, Any]]`: Flat list of all chunks from all documents

**Performance:**
- ~1000 docs/second (chunking is CPU-bound, very fast)

**Example:**
```python
# Fetch documents from Supabase
docs = await supabase.get_context_documents(limit=100)

# Chunk all documents
all_chunks = chunking.chunk_documents_batch(docs)

print(f"{len(docs)} docs → {len(all_chunks)} chunks")
print(f"Average: {len(all_chunks) / len(docs):.1f} chunks/doc")
```

---

#### Method: `estimate_chunks(text: str) -> int`

Estimate number of chunks for a text (without actually splitting).

**Parameters:**
- `text` (str): Text to estimate

**Returns:**
- `int`: Estimated number of chunks

**Formula:**
```python
effective_size = chunk_size - chunk_overlap
estimated = ((text_length - chunk_size) / effective_size) + 1
```

**Example:**
```python
# Estimate chunks before processing
text = "x" * 10000  # 10,000 chars

estimated = chunking.estimate_chunks(text)
print(f"Estimated chunks: {estimated}")  # ~5

actual_chunks = chunking.chunk_document(text, "test-id")
print(f"Actual chunks: {len(actual_chunks)}")  # ~5
```

---

#### Method: `get_config() -> Dict[str, Any]`

Get current chunking configuration.

**Returns:**
- `dict`: Configuration details

**Example:**
```python
config = chunking.get_config()
print(config)
# {
#     'chunk_size': 2048,
#     'chunk_overlap': 200,
#     'overlap_percentage': 9.765625,
#     'separators': ['\\n\\n', '\\n', ' ', ''],
#     'estimated_tokens_per_chunk': 512,
#     'strategy': 'RecursiveCharacterTextSplitter',
#     'optimized_for': ['multilingual', 'OCR text', 'agricultural documents']
# }
```

---

#### Function: `chunk_text(text: str, chunk_size: int = 2048, chunk_overlap: int = 200) -> List[str]`

Quick chunking function without metadata (module-level).

**Parameters:**
- `text` (str): Text to chunk
- `chunk_size` (int): Chunk size
- `chunk_overlap` (int): Overlap size

**Returns:**
- `List[str]`: List of chunk strings (no metadata)

**Example:**
```python
from app.services.chunking_service import chunk_text

# Quick chunking
chunks = chunk_text("Long text...", chunk_size=1000)
print(len(chunks))
```

---

## SemanticSearchService

**Location**: `app/services/semantic_search_service.py`

**Purpose**: Semantic search using Supabase pgvector with HNSW indexing.

### Class: `SemanticSearchService`

#### Constructor

```python
def __init__(
    self,
    supabase: SupabaseService,
    embedding: EmbeddingService
)
```

**Parameters:**
- `supabase` (SupabaseService): Supabase service instance
- `embedding` (EmbeddingService): Embedding service instance

**Example:**
```python
from app.services.supabase_service import SupabaseService
from app.services.embedding_service import EmbeddingService
from app.services.semantic_search_service import SemanticSearchService

supabase = SupabaseService(url, key)
embedding = EmbeddingService()
search = SemanticSearchService(supabase, embedding)
```

---

#### Method: `async search(query: str, top_k: int = 5, similarity_threshold: float = 0.7, commodity: Optional[str] = None, source: Optional[str] = None) -> List[Dict[str, Any]]`

Semantic search in document embeddings.

**Parameters:**
- `query` (str): Search query (any language)
- `top_k` (int): Number of results (default: 5)
- `similarity_threshold` (float): Minimum cosine similarity (default: 0.7)
  - 0.7+ = High relevance
  - 0.6-0.7 = Medium relevance
  - <0.6 = Low relevance
- `commodity` (str, optional): Filter by commodity ('cashew', 'rubber')
- `source` (str, optional): Filter by source ('GDrive', 'ODC', etc.)

**Returns:**
- `List[Dict[str, Any]]`: Search results

**Result Structure:**
```python
{
    'id': 'chunk-uuid',
    'document_id': 'doc-uuid',
    'chunk_index': 2,
    'chunk_text': 'Chunk content...',
    'similarity': 0.8538,  # Cosine similarity (0-1)
    'metadata': {
        'source': 'GDrive',
        'commodity': 'cashew',
        'title': 'iTrade Bulletin',
        'url': 'https://...',
        'chunk_index': 2,
        'total_chunks': 5,
        'char_count': 2048
    }
}
```

**Performance:**
- Query embedding: ~50-100ms (CPU)
- pgvector search: <50ms (HNSW index)
- **Total: <150ms**

**Example:**
```python
# Basic search
results = await search.search(
    query="cashew production statistics",
    top_k=5
)

# With filters
results = await search.search(
    query="export data 2024",
    commodity="rubber",
    source="ODC",
    top_k=10,
    similarity_threshold=0.75
)

# Display results
for result in results:
    print(f"{result['similarity']:.3f} - {result['metadata']['title']}")
```

---

#### Method: `async search_with_context(query: str, top_k: int = 5, commodity: Optional[str] = None) -> str`

Get formatted context string for RAG.

**Parameters:**
- `query` (str): Search query
- `top_k` (int): Number of chunks (default: 5)
- `commodity` (str, optional): Filter by commodity

**Returns:**
- `str`: Formatted context string ready for Perplexity

**Context Format:**
```
[Source 1: GDrive - iTrade Bulletin] (Similarity: 0.85)
Cashew production in Cambodia has increased...

---

[Source 2: ODC - Agricultural Report] (Similarity: 0.82)
Kampong Thom province produces 5,200 tons...

---

[Source 3: ...]
```

**Example:**
```python
# Get context for RAG
context = await search.search_with_context(
    query="Cashew export challenges",
    top_k=5,
    commodity="cashew"
)

# Use with Perplexity
response = await perplexity.rag_query(
    query="What are the main export challenges?",
    retrieved_context=context,
    commodity="cashew"
)
```

---

#### Method: `async get_similar_chunks(chunk_text: str, top_k: int = 3, exclude_document_id: Optional[str] = None) -> List[Dict[str, Any]]`

Find similar chunks to a given chunk (for related content discovery).

**Parameters:**
- `chunk_text` (str): Text to find similar chunks for
- `top_k` (int): Number of similar chunks (default: 3)
- `exclude_document_id` (str, optional): Exclude chunks from this document

**Returns:**
- `List[Dict[str, Any]]`: Similar chunks (same structure as `search()`)

**Use Cases:**
- "Related documents" feature
- Duplicate detection
- Cross-referencing

**Example:**
```python
# Find related content
chunk = "Cashew production statistics for Kampong Thom"
similar = await search.get_similar_chunks(
    chunk,
    top_k=3,
    exclude_document_id="current-doc-id"  # Don't show same doc
)

for s in similar:
    print(f"{s['similarity']:.2f} - {s['metadata']['title']}")
```

---

#### Method: `get_stats() -> Dict[str, Any]`

Get semantic search statistics.

**Returns:**
- `dict`: Service stats

**Example:**
```python
stats = search.get_stats()
print(stats)
# {
#     'embedding_model': 'intfloat/multilingual-e5-large',
#     'embedding_dimension': 1024,
#     'vector_db': 'Supabase pgvector',
#     'index_type': 'HNSW (m=16, ef_construction=64)',
#     'supported_languages': ['Khmer', 'English', 'Vietnamese', '100+ total'],
#     'default_threshold': 0.7,
#     'default_top_k': 5,
#     'cost': '$0 (Supabase free tier + local embeddings)',
#     'performance': '<100ms per query (with HNSW index)'
# }
```

---

## PerplexityService

**Location**: `app/services/perplexity_service.py`

**Purpose**: Perplexity API integration for RAG and market research.

### Class: `PerplexityService`

#### Constructor

```python
def __init__(self, api_key: str, max_requests_per_month: int = 1000)
```

**Parameters:**
- `api_key` (str): Perplexity API key
- `max_requests_per_month` (int): Rate limit (default: 1000)

**Example:**
```python
from app.services.perplexity_service import PerplexityService

perplexity = PerplexityService(
    api_key="pplx-xxxxx",
    max_requests_per_month=1000
)
```

---

#### Method: `async rag_query(query: str, retrieved_context: str, commodity: str) -> Dict[str, Any]`

RAG query with context from local documents.

**Parameters:**
- `query` (str): User question
- `retrieved_context` (str): Context from semantic search
- `commodity` (str): Commodity name ('cashew', 'rubber')

**Returns:**
- `dict`: Response with answer and metadata

**Response Structure:**
```python
{
    'commodity': 'cashew',
    'query_type': 'rag',
    'query_text': 'What are export volumes?',
    'response_text': 'According to the iTrade Bulletin...',
    'citations': [
        'https://source1.com',
        'https://source2.com'
    ],
    'created_at': '2024-12-26T10:00:00',
    'metadata': {
        'model': 'sonar-pro',
        'tokens_used': 2847,
        'request_id': 'req_xxxxx',
        'context_length': 8432
    }
}
```

**Performance:**
- Perplexity API call: 2-5 seconds
- Depends on context size and response length

**Cost:**
- ~$0.005 per query
- ~$5 for 1000 queries/month

**Example:**
```python
# Step 1: Get context
context = await search.search_with_context(
    query="Cashew export statistics",
    commodity="cashew",
    top_k=5
)

# Step 2: RAG query
result = await perplexity.rag_query(
    query="What are the latest cashew export volumes?",
    retrieved_context=context,
    commodity="cashew"
)

# Step 3: Display answer
print(result['response_text'])
print(f"\nCitations: {result['citations']}")
print(f"Tokens: {result['metadata']['tokens_used']}")
```

---

#### Method: `get_stats() -> Dict[str, Any]`

Get service statistics and quota usage.

**Returns:**
- `dict`: Usage statistics

**Example:**
```python
stats = perplexity.get_stats()
print(stats)
# {
#     'requests_used': 45,
#     'requests_remaining': 955,
#     'rate_limit': 1000,
#     'utilization_percentage': 4.5
# }
```

---

#### Method: `reset_counter() -> None`

Reset monthly request counter.

**Usage:** Call at start of each month

**Example:**
```python
# Reset counter on 1st of month
from datetime import datetime

if datetime.now().day == 1:
    perplexity.reset_counter()
    print("Perplexity counter reset for new month")
```

---

## Database Schema

### Table: `document_embeddings`

**Purpose:** Store document chunks with embeddings for vector search.

```sql
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES context_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1024) NOT NULL,  -- pgvector type
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Index for vector similarity search (HNSW)
    -- m=16: max connections per node
    -- ef_construction=64: build-time accuracy
    INDEX idx_embedding_hnsw ON document_embeddings
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
);
```

**Columns:**
- `id`: Unique chunk ID (UUID)
- `document_id`: Foreign key to source document
- `chunk_index`: Position within document (0-based)
- `chunk_text`: Actual text content of chunk
- `embedding`: 1024-dimensional vector
- `metadata`: JSON metadata (source, commodity, title, etc.)
- `created_at`: Timestamp

**Indexes:**
- `idx_embedding_hnsw`: HNSW index for fast vector search

---

### RPC Function: `match_documents`

**Purpose:** Perform similarity search on embeddings.

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
        -- Similarity filter
        (1 - (de.embedding <=> query_embedding)) >= match_threshold
        -- Commodity filter (if provided)
        AND (filter_commodity IS NULL OR de.metadata->>'commodity' = filter_commodity)
    ORDER BY de.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

**Parameters:**
- `query_embedding`: Query vector (1024 dimensions)
- `match_count`: Number of results (default: 5)
- `match_threshold`: Minimum similarity (default: 0.7)
- `filter_commodity`: Optional commodity filter

**Returns:**
- Table with matching chunks and similarity scores

**Operator:** `<=>` is cosine distance (1 - similarity)

---

## Integration Guide

### Complete RAG Integration Example

```python
"""
Complete RAG integration example.
Demonstrates all Phase 3 services working together.
"""
import asyncio
from app.config import settings
from app.services.supabase_service import SupabaseService
from app.services.embedding_service import EmbeddingService
from app.services.chunking_service import ChunkingService
from app.services.semantic_search_service import SemanticSearchService
from app.services.perplexity_service import PerplexityService


async def main():
    # 1. Initialize all services
    print("Initializing services...")
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
    embedding = EmbeddingService()
    chunking = ChunkingService()
    search = SemanticSearchService(supabase, embedding)
    perplexity = PerplexityService(
        api_key=settings.perplexity_api_key,
        max_requests_per_month=1000
    )

    # 2. (One-time) Process new documents
    print("\n[Optional] Processing new documents...")
    docs = await supabase.get_context_documents(limit=5)

    for doc in docs:
        # Chunk document
        chunks = chunking.chunk_document(
            doc['text_content'],
            doc['id'],
            metadata={
                'source': doc['source'],
                'commodity': doc['commodity'],
                'title': doc['title']
            }
        )

        # Generate embeddings
        chunk_texts = [c['chunk_text'] for c in chunks]
        embeddings = embedding.embed_batch(chunk_texts, show_progress=False)

        # Store in Supabase
        for chunk, emb in zip(chunks, embeddings):
            supabase.client.table("document_embeddings").insert({
                "document_id": chunk['document_id'],
                "chunk_index": chunk['chunk_index'],
                "chunk_text": chunk['chunk_text'],
                "embedding": emb,
                "metadata": chunk['metadata']
            }).execute()

    # 3. User query (interactive)
    user_question = "What are the main challenges for cashew farmers?"
    commodity = "cashew"

    print(f"\nUser Question: {user_question}")

    # 4. Semantic search for context
    print("Searching documents...")
    context = await search.search_with_context(
        query=user_question,
        top_k=5,
        commodity=commodity
    )

    print(f"Found context: {len(context)} chars from {context.count('---') + 1} chunks")

    # 5. Generate RAG answer
    print("Generating AI answer...")
    result = await perplexity.rag_query(
        query=user_question,
        retrieved_context=context,
        commodity=commodity
    )

    # 6. Display results
    print("\n" + "="*80)
    print("ANSWER:")
    print("="*80)
    print(result['response_text'])

    if result.get('citations'):
        print(f"\n\nCitations ({len(result['citations'])}):")
        for i, citation in enumerate(result['citations'], 1):
            print(f"  [{i}] {citation}")

    # 7. Show stats
    print("\n" + "="*80)
    print("STATISTICS:")
    print("="*80)
    print(f"Tokens used: {result['metadata']['tokens_used']}")
    print(f"Model: {result['metadata']['model']}")

    perp_stats = perplexity.get_stats()
    print(f"Perplexity usage: {perp_stats['requests_used']}/{perp_stats['rate_limit']}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## API Best Practices

### 1. Service Initialization

**DO:**
```python
# Initialize once, reuse across requests
embedding = EmbeddingService()  # Singleton
search = SemanticSearchService(supabase, embedding)
```

**DON'T:**
```python
# Initialize in every request (slow!)
async def handle_request():
    embedding = EmbeddingService()  # ❌ Reloads model each time
    ...
```

### 2. Error Handling

```python
try:
    results = await search.search(query, top_k=5)
except Exception as e:
    logger.error(f"Search failed: {e}")
    # Fallback or user-friendly error
    results = []
```

### 3. Rate Limiting

```python
# Check Perplexity quota before query
stats = perplexity.get_stats()
if stats['requests_remaining'] < 10:
    print("Warning: Low Perplexity quota!")
    # Maybe switch to semantic search only
```

### 4. Batch Processing

```python
# DO: Batch embed for efficiency
embeddings = embedding.embed_batch(texts, batch_size=32)

# DON'T: Individual calls (slow)
embeddings = [embedding.embed_text(t) for t in texts]
```

---

**For more information:**
- Setup: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- Performance: [PERFORMANCE.md](PERFORMANCE.md)
- Troubleshooting: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
