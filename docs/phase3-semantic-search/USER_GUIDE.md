# User Guide: Semantic Search & RAG System

## Table of Contents

1. [Introduction](#introduction)
2. [Use Cases](#use-cases)
3. [Semantic Search](#semantic-search)
4. [RAG (Retrieval-Augmented Generation)](#rag-retrieval-augmented-generation)
5. [Multilingual Support](#multilingual-support)
6. [Best Practices](#best-practices)
7. [Examples](#examples)

## Introduction

The Phase 3 Semantic Search & RAG system allows you to:
- Search agricultural documents by meaning (not just keywords)
- Ask questions in natural language and get AI-generated answers
- Work in multiple languages (Khmer, English, Vietnamese)
- Get answers based on your local document collection

### What is Semantic Search?

Traditional keyword search finds exact word matches. Semantic search understands **meaning**:

**Keyword Search:**
- Query: "cashew production"
- Finds: Documents containing exactly "cashew production"
- Misses: Documents about "anacardium processing" or "ការផលិតស្វាយចន្ទី"

**Semantic Search:**
- Query: "cashew production"
- Finds: Documents about cashew cultivation, anacardium processing, nut farming, AND "ការផលិតស្វាយចន្ទី" (Khmer)
- Understands: Synonyms, translations, and related concepts

### What is RAG?

RAG (Retrieval-Augmented Generation) combines:
1. **Retrieval**: Find relevant document chunks (semantic search)
2. **Augmentation**: Add context to your question
3. **Generation**: AI generates an answer based on your documents

**Benefits:**
- Answers based on YOUR documents (not generic AI knowledge)
- Citations and sources included
- Combines local + online information when needed

## Use Cases

### 1. Document Discovery

**Scenario**: You have 100+ agricultural reports and need to find relevant information quickly.

```python
# Find documents about specific topics
results = await search.search(
    query="rubber latex quality standards",
    top_k=10,
    commodity="rubber"
)
```

**Output**: Top 10 most relevant document chunks, ranked by similarity.

### 2. Q&A for Researchers

**Scenario**: You need specific facts from your document collection.

```python
# Ask natural language questions
answer = await perplexity.rag_query(
    query="What are the export volumes for Cambodian cashew in 2024?",
    retrieved_context=context,  # From semantic search
    commodity="cashew"
)
```

**Output**: AI-generated answer citing your local documents.

### 3. Multilingual Research

**Scenario**: You have documents in multiple languages and want to search across them.

```python
# Search in Khmer, find results in any language
results = await search.search(
    query="ការផលិតកៅស៊ូ",  # Khmer: "rubber production"
    top_k=5
)

# Results may include English, Vietnamese, and Khmer documents
```

### 4. Market Intelligence

**Scenario**: Combine local reports with online market data.

```python
# RAG query combines local + online sources
answer = await perplexity.rag_query(
    query="How do recent geopolitical events affect Cambodia cashew exports?",
    retrieved_context=local_context,
    commodity="cashew"
)
```

**Output**: Answer based on your reports + latest online news.

## Semantic Search

### Basic Search

```python
import asyncio
from app.services.supabase_service import SupabaseService
from app.services.embedding_service import EmbeddingService
from app.services.semantic_search_service import SemanticSearchService
from app.config import settings

async def search_example():
    # Initialize services
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
    embedding = EmbeddingService()
    search = SemanticSearchService(supabase, embedding)

    # Search
    results = await search.search(
        query="cashew processing facilities",
        top_k=5,
        similarity_threshold=0.7
    )

    # Display results
    for i, result in enumerate(results, 1):
        print(f"\n[{i}] Similarity: {result['similarity']:.4f}")
        print(f"Source: {result['metadata']['source']}")
        print(f"Title: {result['metadata']['title']}")
        print(f"Text: {result['chunk_text'][:300]}...")

asyncio.run(search_example())
```

### Understanding Similarity Scores

| Score Range | Interpretation | Use Case |
|-------------|----------------|----------|
| 0.9 - 1.0 | Nearly identical | Exact matches, duplicates |
| 0.8 - 0.9 | Highly similar | Very relevant results |
| 0.7 - 0.8 | Similar | Relevant results (default threshold) |
| 0.6 - 0.7 | Somewhat similar | Potentially relevant |
| < 0.6 | Loosely related | Usually filtered out |

**Recommendation**: Use `similarity_threshold=0.7` for most queries.

### Filtering Results

#### By Commodity

```python
# Only cashew-related documents
results = await search.search(
    query="export statistics 2024",
    commodity="cashew",  # Filter by commodity
    top_k=5
)
```

#### By Source

```python
# Only documents from Google Drive
results = await search.search(
    query="market analysis",
    source="GDrive",  # Filter by source
    top_k=5
)
```

#### Combined Filters

```python
# Rubber documents from ODC only
results = await search.search(
    query="plantation areas",
    commodity="rubber",
    source="ODC",
    top_k=5
)
```

### Getting Context for RAG

```python
# Get formatted context string (ready for Perplexity)
context = await search.search_with_context(
    query="cashew production challenges",
    top_k=5,
    commodity="cashew"
)

print(context)
# Output:
# [Source 1: GDrive - iTrade Bulletin] (Similarity: 0.85)
# Cashew production in Cambodia faces several challenges...
#
# ---
#
# [Source 2: ODC - Agricultural Report] (Similarity: 0.82)
# Processing capacity remains limited in rural areas...
```

## RAG (Retrieval-Augmented Generation)

### Complete RAG Workflow

```python
import asyncio
from app.config import settings
from app.services.supabase_service import SupabaseService
from app.services.embedding_service import EmbeddingService
from app.services.semantic_search_service import SemanticSearchService
from app.services.perplexity_service import PerplexityService

async def rag_example():
    # Step 1: Initialize services
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
    embedding = EmbeddingService()
    search = SemanticSearchService(supabase, embedding)
    perplexity = PerplexityService(
        api_key=settings.perplexity_api_key,
        max_requests_per_month=1000
    )

    # Step 2: User question
    question = "What are the main export destinations for Cambodian cashew?"

    # Step 3: Retrieve relevant context from local documents
    context = await search.search_with_context(
        query=question,
        top_k=5,
        commodity="cashew"
    )

    # Step 4: Generate answer using RAG
    result = await perplexity.rag_query(
        query=question,
        retrieved_context=context,
        commodity="cashew"
    )

    # Step 5: Display answer
    print("QUESTION:")
    print(question)
    print("\nANSWER:")
    print(result['response_text'])
    print("\nCITATIONS:")
    for citation in result.get('citations', []):
        print(f"- {citation}")
    print(f"\nTokens used: {result['metadata'].get('tokens_used', 'N/A')}")

asyncio.run(rag_example())
```

### Understanding RAG Responses

RAG responses should:
1. **Cite local documents** when available
2. **Distinguish** between local and external sources
3. **Provide specific data** (numbers, dates, facts)
4. **Include citations** for verification

**Example Response:**
```
Based on local documents, the main export destinations for Cambodian cashew are:

1. **Vietnam** (60-70% of raw nuts): According to the iTrade Bulletin Q2 2024,
   Vietnam processes most of Cambodia's raw cashew exports, with approximately
   45,000 tons exported annually.

2. **China** (15-20%): The ODC Agricultural Report indicates growing demand
   from Chinese processors, particularly for premium grades.

3. **Europe** (5-10% of processed kernels): Direct exports of processed
   cashew kernels to European markets, primarily Germany and Netherlands.

Based on external sources, recent trade agreements with the EU have reduced
tariffs by 12%, potentially increasing European exports in 2025.
```

### RAG Best Practices

#### 1. Be Specific

**Good**: "What are cashew export volumes to Vietnam in Q2 2024?"
**Bad**: "Tell me about cashews"

#### 2. Match Document Content

If your documents focus on production (not pricing), ask about production.

**Good** (if docs contain production data):
- "How many tons of cashew does Kampong Thom produce?"
- "What are the main cashew growing provinces?"

**Less Good** (if docs lack price data):
- "What is the current price per kg?"

#### 3. Use Commodity Filters

```python
# More accurate (filtered context)
context = await search.search_with_context(
    query="export statistics",
    commodity="rubber",  # Only rubber docs
    top_k=5
)

# Less accurate (mixed context)
context = await search.search_with_context(
    query="export statistics",
    # No filter - may mix cashew + rubber
    top_k=5
)
```

#### 4. Monitor API Usage

```python
# Check Perplexity usage
stats = perplexity.get_stats()
print(f"Requests used: {stats['requests_used']}/{stats['rate_limit']}")
print(f"Remaining: {stats['requests_remaining']}")
```

**Budget Management:**
- Free tier: 1000 requests/month
- Cost: ~$0.005 per query
- Monthly cost: $5 for 1000 queries

## Multilingual Support

### Supported Languages

The system supports **100+ languages**, including:
- **Khmer** (ភាសាខ្មែរ)
- **English**
- **Vietnamese** (Tiếng Việt)
- French, Thai, Chinese, and more

### Cross-Lingual Search

Search in one language, find results in any language:

```python
# Query in Khmer
results = await search.search(
    query="ការផលិតស្វាយចន្ទី",  # Khmer: "cashew production"
    top_k=5
)

# Results may include:
# - English documents about "cashew production"
# - Vietnamese documents about "sản xuất điều"
# - Khmer documents about "ស្វាយចន្ទី"
```

### How It Works

The embedding model (`multilingual-e5-large`) maps text from different languages into the same semantic space:

```
Khmer:      "ការផលិតស្វាយចន្ទី"      → [0.234, -0.567, 0.891, ...]
English:    "cashew production"      → [0.229, -0.571, 0.885, ...]
Vietnamese: "sản xuất điều"          → [0.241, -0.560, 0.893, ...]
                                         ↑ Very similar vectors!
```

### Language Best Practices

1. **Use natural language** (no need to translate)
2. **Mix languages in queries** if needed
3. **Results rank by semantic similarity** (not language)

## Best Practices

### 1. Query Formulation

#### Good Queries
- Specific questions: "What are cashew yields in Kampong Thom province?"
- Domain terms: "rubber latex quality standards TSR20"
- Natural language: "How does weather affect cashew flowering?"

#### Poor Queries
- Too broad: "agriculture"
- Single words: "cashew"
- Unrelated: "weather forecast tomorrow"

### 2. Result Interpretation

#### Similarity Scores
- **0.85+**: Highly relevant, trust the result
- **0.75-0.85**: Relevant, good match
- **0.70-0.75**: Potentially relevant, review content
- **<0.70**: May be off-topic (adjust `similarity_threshold`)

#### Multiple Results
- Review top 3-5 results (not just #1)
- Compare information across sources
- Check metadata (source, date, commodity)

### 3. Performance Optimization

#### Adjust `top_k` Based on Need
```python
# Quick overview
results = await search.search(query, top_k=3)

# Comprehensive research
results = await search.search(query, top_k=10)

# RAG context (balance quality vs. token cost)
context = await search.search_with_context(query, top_k=5)  # Recommended
```

#### Use Filters
```python
# Faster (smaller search space)
results = await search.search(
    query="statistics",
    commodity="cashew",  # Filter reduces computation
    top_k=5
)
```

### 4. Cost Management

#### Semantic Search: Free
- Local embeddings: $0
- Supabase queries: $0 (free tier: 50GB storage, 500MB/month transfer)

#### RAG Queries: ~$0.005 each
- Monitor usage:
```python
stats = perplexity.get_stats()
if stats['requests_remaining'] < 100:
    print("Warning: Low Perplexity quota")
```

- Reset counter monthly:
```python
perplexity.reset_counter()  # Call at start of each month
```

## Examples

### Example 1: Find Documents About Processing

```python
async def find_processing_info():
    search = SemanticSearchService(supabase, embedding)

    results = await search.search(
        query="cashew processing facilities equipment",
        commodity="cashew",
        top_k=5,
        similarity_threshold=0.7
    )

    print(f"Found {len(results)} relevant chunks:\n")

    for i, result in enumerate(results, 1):
        metadata = result['metadata']
        print(f"[{i}] Similarity: {result['similarity']:.3f}")
        print(f"    Source: {metadata['source']} - {metadata['title']}")
        print(f"    Snippet: {result['chunk_text'][:150]}...")
        print()
```

### Example 2: Multi-Language Search

```python
async def multilingual_search():
    search = SemanticSearchService(supabase, embedding)

    # Search in different languages
    queries = [
        "cashew export statistics",      # English
        "ស្ថិតិនាំចេញស្វាយចន្ទី",        # Khmer
        "thống kê xuất khẩu điều"        # Vietnamese
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        results = await search.search(query, top_k=3)

        for result in results:
            print(f"  - {result['metadata']['title'][:50]}")
            print(f"    Similarity: {result['similarity']:.3f}")
```

### Example 3: Compare Local vs. RAG

```python
async def compare_search_vs_rag():
    search = SemanticSearchService(supabase, embedding)
    perplexity = PerplexityService(settings.perplexity_api_key)

    question = "What challenges do smallholder cashew farmers face?"

    # Method 1: Direct semantic search
    print("METHOD 1: Semantic Search\n" + "="*50)
    results = await search.search(question, commodity="cashew", top_k=3)
    for result in results:
        print(f"Similarity: {result['similarity']:.3f}")
        print(f"Text: {result['chunk_text'][:200]}...\n")

    # Method 2: RAG (AI-generated answer)
    print("\nMETHOD 2: RAG (AI Answer)\n" + "="*50)
    context = await search.search_with_context(question, commodity="cashew", top_k=5)
    rag_result = await perplexity.rag_query(question, context, "cashew")
    print(rag_result['response_text'])
    print(f"\nCitations: {len(rag_result.get('citations', []))}")
```

### Example 4: Interactive Q&A Session

```python
async def interactive_qa():
    """Interactive Q&A session with RAG."""
    search = SemanticSearchService(supabase, embedding)
    perplexity = PerplexityService(settings.perplexity_api_key)

    commodity = input("Commodity (cashew/rubber): ").strip()

    while True:
        question = input("\nYour question (or 'quit'): ").strip()

        if question.lower() in ['quit', 'exit', 'q']:
            break

        # Retrieve context
        print("Searching documents...")
        context = await search.search_with_context(
            query=question,
            top_k=5,
            commodity=commodity
        )

        # Generate answer
        print("Generating answer...")
        result = await perplexity.rag_query(question, context, commodity)

        # Display
        print("\n" + "="*70)
        print("ANSWER:")
        print("="*70)
        print(result['response_text'])

        if result.get('citations'):
            print(f"\nSources ({len(result['citations'])}):")
            for citation in result['citations'][:3]:
                print(f"  - {citation}")

        # Show usage
        stats = perplexity.get_stats()
        print(f"\n[Perplexity usage: {stats['requests_used']}/{stats['rate_limit']}]")
```

## Next Steps

- **Technical Details**: See [TECHNICAL_REFERENCE.md](TECHNICAL_REFERENCE.md)
- **Setup Instructions**: See [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Performance Tuning**: See [PERFORMANCE.md](PERFORMANCE.md)
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**For support or questions, refer to the complete documentation suite.**
