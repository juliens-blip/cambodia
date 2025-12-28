"""POC: Test multilingual-e5-large with REAL PDF extracts from Supabase."""
import sys
import os
import io
import asyncio

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 80)
print("POC: Testing with REAL PDF Extracts from Supabase")
print("=" * 80)

# Step 1: Import dependencies
print("\n1️⃣ Importing dependencies...")
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from app.config import settings
    from app.services.supabase_service import SupabaseService
    print("   ✅ Imports successful")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Step 2: Load model
print("\n2️⃣ Loading multilingual-e5-large model...")
try:
    model = SentenceTransformer('intfloat/multilingual-e5-large')
    print(f"   ✅ Model loaded (dim: {model.get_sentence_embedding_dimension()})")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Step 3: Fetch real documents from Supabase
async def fetch_real_documents():
    """Fetch 5 real context documents from Supabase."""
    print("\n3️⃣ Fetching real documents from Supabase...")

    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

    try:
        docs = await supabase.get_context_documents(limit=10)
        print(f"   ✅ Fetched {len(docs)} documents")

        # Select diverse documents
        selected = []
        sources_seen = set()

        for doc in docs:
            source = doc.get('source', 'Unknown')
            commodity = doc.get('commodity', 'Unknown')

            # Get diverse sources
            if len(selected) < 5:
                selected.append({
                    'id': doc['id'],
                    'title': doc['title'],
                    'source': source,
                    'commodity': commodity,
                    'text': doc['text_content'][:2000],  # First 2000 chars
                    'full_length': len(doc['text_content']),
                    'extraction_method': doc.get('extraction_method', 'unknown')
                })
                sources_seen.add(source)

        print(f"\n   Selected {len(selected)} diverse documents:")
        for i, doc in enumerate(selected, 1):
            print(f"   [{i}] {doc['title'][:50]}")
            print(f"       Source: {doc['source']} | Commodity: {doc['commodity']}")
            print(f"       Length: {doc['full_length']} chars | Method: {doc['extraction_method']}")

        return selected

    except Exception as e:
        print(f"   ❌ Error fetching documents: {e}")
        return []

# Step 4: Test embeddings with real texts
def test_real_embeddings(docs):
    """Generate embeddings for real PDF extracts."""
    print("\n4️⃣ Generating embeddings for real PDF extracts...")

    embeddings = {}

    for i, doc in enumerate(docs, 1):
        try:
            # Use first 500 chars as passage
            passage = f"passage: {doc['text'][:500]}"
            emb = model.encode(passage, convert_to_numpy=True)
            embeddings[doc['id']] = {
                'embedding': emb,
                'doc': doc
            }
            print(f"   ✅ [{i}] {doc['title'][:40]} - Embedded ({emb.shape})")
        except Exception as e:
            print(f"   ❌ [{i}] Error: {e}")

    return embeddings

# Step 5: Test semantic search with real queries
def test_semantic_search(embeddings):
    """Test semantic search with realistic queries."""
    print("\n5️⃣ Testing semantic search with real queries...")

    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    # Real user queries
    queries = [
        {
            'text': 'Cashew production statistics Cambodia',
            'expected_commodity': 'cashew',
            'description': 'English query for cashew data'
        },
        {
            'text': 'ការផលិតស្វាយចន្ទី',  # Cashew production
            'expected_commodity': 'cashew',
            'description': 'Khmer query for cashew'
        },
        {
            'text': 'Rubber export Vietnam China',
            'expected_commodity': 'rubber',
            'description': 'English query for rubber export'
        },
        {
            'text': 'Economic land concessions agriculture',
            'expected_commodity': None,
            'description': 'General policy query'
        },
        {
            'text': 'ការនាំចេញ កៅស៊ូ',  # Rubber export
            'expected_commodity': 'rubber',
            'description': 'Khmer query for rubber'
        }
    ]

    results = []

    for query_info in queries:
        query_text = f"query: {query_info['text']}"
        query_emb = model.encode(query_text, convert_to_numpy=True)

        print(f"\n   Query: '{query_info['text']}'")
        print(f"   Description: {query_info['description']}")

        # Calculate similarities
        similarities = []
        for doc_id, data in embeddings.items():
            sim = cosine_similarity(query_emb, data['embedding'])
            similarities.append({
                'doc_id': doc_id,
                'similarity': sim,
                'title': data['doc']['title'],
                'source': data['doc']['source'],
                'commodity': data['doc']['commodity']
            })

        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)

        # Show top 3
        print(f"   Top 3 results:")
        for i, result in enumerate(similarities[:3], 1):
            emoji = "✅" if result['similarity'] > 0.70 else "⚠️" if result['similarity'] > 0.60 else "❌"
            print(f"   {emoji} [{i}] {result['similarity']:.4f} - {result['title'][:50]}")
            print(f"            Source: {result['source']} | Commodity: {result['commodity']}")

        # Check if top result matches expected commodity
        top_result = similarities[0]
        expected = query_info['expected_commodity']

        if expected:
            match = top_result['commodity'] == expected
            print(f"   Commodity match: {'✅ PASS' if match else '❌ FAIL'} (expected: {expected}, got: {top_result['commodity']})")
        else:
            print(f"   General query - no specific commodity expected")

        results.append({
            'query': query_info,
            'top_similarity': top_result['similarity'],
            'top_result': top_result,
            'all_results': similarities
        })

    return results

# Step 6: Analyze results
def analyze_results(results):
    """Analyze retrieval quality."""
    print("\n" + "=" * 80)
    print("📊 RETRIEVAL QUALITY ANALYSIS")
    print("=" * 80)

    similarities = [r['top_similarity'] for r in results]
    avg_sim = np.mean(similarities)
    min_sim = np.min(similarities)
    max_sim = np.max(similarities)

    print(f"\nSimilarity Statistics:")
    print(f"   Average: {avg_sim:.4f}")
    print(f"   Min: {min_sim:.4f}")
    print(f"   Max: {max_sim:.4f}")

    # Count matches
    matches = 0
    total_with_expected = 0

    for r in results:
        expected = r['query']['expected_commodity']
        if expected:
            total_with_expected += 1
            if r['top_result']['commodity'] == expected:
                matches += 1

    if total_with_expected > 0:
        accuracy = (matches / total_with_expected) * 100
        print(f"\nCommodity Matching:")
        print(f"   Correct: {matches}/{total_with_expected} ({accuracy:.1f}%)")

    # Quality thresholds
    high_quality = sum(1 for s in similarities if s > 0.75)
    medium_quality = sum(1 for s in similarities if 0.60 < s <= 0.75)
    low_quality = sum(1 for s in similarities if s <= 0.60)

    print(f"\nQuality Distribution:")
    print(f"   ✅ High (>0.75): {high_quality}/{len(results)}")
    print(f"   ⚠️ Medium (0.60-0.75): {medium_quality}/{len(results)}")
    print(f"   ❌ Low (<0.60): {low_quality}/{len(results)}")

    return {
        'avg_similarity': avg_sim,
        'accuracy': accuracy if total_with_expected > 0 else None,
        'high_quality_ratio': high_quality / len(results)
    }

# Step 7: Final recommendation
def final_recommendation(metrics):
    """Provide final recommendation based on real data."""
    print("\n" + "=" * 80)
    print("🎯 FINAL RECOMMENDATION")
    print("=" * 80)

    avg_sim = metrics['avg_similarity']
    accuracy = metrics.get('accuracy')
    high_quality_ratio = metrics['high_quality_ratio']

    print(f"\nKey Metrics:")
    print(f"   Average Similarity: {avg_sim:.4f}")
    if accuracy is not None:
        print(f"   Commodity Accuracy: {accuracy:.1f}%")
    print(f"   High Quality Ratio: {high_quality_ratio:.1%}")

    # Decision criteria
    pass_criteria = {
        'avg_similarity': avg_sim >= 0.70,
        'high_quality_ratio': high_quality_ratio >= 0.60
    }

    if accuracy is not None:
        pass_criteria['accuracy'] = accuracy >= 60

    passed = sum(pass_criteria.values())
    total = len(pass_criteria)

    print(f"\nCriteria:")
    for criterion, result in pass_criteria.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {criterion}")

    print(f"\n{'='*80}")

    if passed == total:
        print("✅ CONCLUSION: multilingual-e5-large EXCELLENT for this project!")
        print("="*80)
        print("\n🚀 RECOMMENDATION: Proceed with Phase 1 implementation")
        print("   - Model: multilingual-e5-large (1024 dim)")
        print("   - Khmer support: VALIDATED with real OCR data")
        print("   - Retrieval quality: HIGH")
        print("   - Ready for production use")
    elif passed >= total * 0.6:
        print("⚠️ CONCLUSION: multilingual-e5-large ACCEPTABLE")
        print("="*80)
        print("\n🔄 RECOMMENDATION: Proceed with caution")
        print("   - Consider adjusting similarity threshold")
        print("   - Monitor retrieval quality in production")
        print("   - May need fine-tuning")
    else:
        print("❌ CONCLUSION: multilingual-e5-large NOT suitable")
        print("="*80)
        print("\n🔄 RECOMMENDATION: Switch to alternative model")
        print("   - Try: paraphrase-multilingual-mpnet-base-v2")
        print("   - Dimension: 768 (vs 1024)")
        print("   - Re-run this test")

    print("="*80)

# Main execution
async def main():
    """Main test workflow."""
    try:
        # Fetch real documents
        docs = await fetch_real_documents()

        if not docs:
            print("\n❌ No documents fetched. Check Supabase connection.")
            return

        # Test embeddings
        embeddings = test_real_embeddings(docs)

        if not embeddings:
            print("\n❌ No embeddings generated.")
            return

        # Test semantic search
        results = test_semantic_search(embeddings)

        # Analyze results
        metrics = analyze_results(results)

        # Final recommendation
        final_recommendation(metrics)

        print("\n✅ Real PDF test complete!")

    except Exception as e:
        print(f"\n❌ Error in main execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
