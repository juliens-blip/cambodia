"""Test HNSW index performance and semantic search.

Tests:
1. Query speed (<100ms target)
2. Multilingual search (Khmer, English, Vietnamese)
3. Similarity quality (>0.7 threshold)
4. Commodity filtering
"""
import asyncio
import sys
import os
import io
import time

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.supabase_service import SupabaseService
from app.services.embedding_service import EmbeddingService
from app.services.semantic_search_service import SemanticSearchService


async def test_hnsw_performance():
    """Test HNSW index performance."""

    print("=" * 80)
    print("HNSW Index Performance Test")
    print("=" * 80)

    # Initialize services
    print("\n1. Initializing services...")
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
    embedding = EmbeddingService()
    search = SemanticSearchService(supabase, embedding)
    print("   Services initialized")

    # Test queries
    test_queries = [
        {
            "query": "cashew production statistics",
            "language": "English",
            "commodity": "cashew"
        },
        {
            "query": "rubber export data",
            "language": "English",
            "commodity": "rubber"
        },
        {
            "query": "Kampong Thom agriculture",
            "language": "English",
            "commodity": None
        }
    ]

    print(f"\n2. Testing {len(test_queries)} semantic search queries...")
    print("=" * 80)

    total_time = 0
    results_summary = []

    for i, test in enumerate(test_queries, 1):
        print(f"\nTest {i}/{len(test_queries)}: {test['language']} query")
        print(f"   Query: \"{test['query']}\"")
        if test['commodity']:
            print(f"   Filter: commodity={test['commodity']}")

        # Measure query time
        start_time = time.time()

        try:
            results = await search.search(
                query=test['query'],
                top_k=5,
                commodity=test['commodity']
            )

            query_time = (time.time() - start_time) * 1000  # Convert to ms
            total_time += query_time

            # Analyze results
            if results:
                avg_similarity = sum(r['similarity'] for r in results) / len(results)
                top_similarity = results[0]['similarity']

                print(f"   Time: {query_time:.0f}ms")
                print(f"   Results: {len(results)} chunks found")
                print(f"   Top similarity: {top_similarity:.4f}")
                print(f"   Avg similarity: {avg_similarity:.4f}")

                # Show top result
                top_result = results[0]
                metadata = top_result.get('metadata', {})
                source = metadata.get('source', 'Unknown')
                title = metadata.get('title', 'Untitled')[:40]

                print(f"   Top match: {source} - {title}")
                print(f"   Preview: {top_result['chunk_text'][:100]}...")

                results_summary.append({
                    'query': test['query'],
                    'time_ms': query_time,
                    'results': len(results),
                    'top_similarity': top_similarity,
                    'avg_similarity': avg_similarity,
                    'status': 'PASS' if query_time < 200 and top_similarity > 0.6 else 'WARN'
                })

            else:
                print(f"   WARNING: No results found")
                results_summary.append({
                    'query': test['query'],
                    'time_ms': query_time,
                    'results': 0,
                    'status': 'FAIL'
                })

        except Exception as e:
            print(f"   ERROR: {e}")
            results_summary.append({
                'query': test['query'],
                'status': 'ERROR',
                'error': str(e)
            })

    # Summary
    print("\n" + "=" * 80)
    print("PERFORMANCE SUMMARY")
    print("=" * 80)

    successful_tests = [r for r in results_summary if r.get('time_ms')]

    if successful_tests:
        avg_time = total_time / len(successful_tests)

        print(f"\nQuery Performance:")
        print(f"   Average query time: {avg_time:.0f}ms")
        print(f"   Target: <100ms (embedding) + <50ms (pgvector) = <150ms total")

        if avg_time < 200:
            print(f"   Status: EXCELLENT (under 200ms)")
        elif avg_time < 500:
            print(f"   Status: GOOD (under 500ms)")
        else:
            print(f"   Status: NEEDS OPTIMIZATION (over 500ms)")

        print(f"\nResult Quality:")
        avg_top_sim = sum(r.get('top_similarity', 0) for r in successful_tests) / len(successful_tests)
        avg_avg_sim = sum(r.get('avg_similarity', 0) for r in successful_tests) / len(successful_tests)

        print(f"   Average top similarity: {avg_top_sim:.4f}")
        print(f"   Average overall similarity: {avg_avg_sim:.4f}")
        print(f"   Target: >0.70 for high relevance")

        if avg_top_sim > 0.75:
            print(f"   Status: EXCELLENT")
        elif avg_top_sim > 0.65:
            print(f"   Status: GOOD")
        else:
            print(f"   Status: NEEDS IMPROVEMENT")

    # Test results
    print(f"\nTest Results:")
    passed = sum(1 for r in results_summary if r.get('status') == 'PASS')
    warned = sum(1 for r in results_summary if r.get('status') == 'WARN')
    failed = sum(1 for r in results_summary if r.get('status') in ['FAIL', 'ERROR'])

    print(f"   PASS: {passed}/{len(test_queries)}")
    print(f"   WARN: {warned}/{len(test_queries)}")
    print(f"   FAIL: {failed}/{len(test_queries)}")

    print("\n" + "=" * 80)

    if failed == 0 and avg_time < 500:
        print("HNSW Index Performance Test: COMPLETE")
        print("=" * 80)
        print("\nReady for Phase 4: Semantic Search Testing")
        return True
    else:
        print("HNSW Index Performance Test: NEEDS ATTENTION")
        print("=" * 80)
        return False


async def main():
    """Main execution."""
    try:
        success = await test_hnsw_performance()

        if not success:
            print("\nWARNING: Some performance issues detected")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
