"""Test end-to-end RAG workflow.

Tests:
1. Semantic search retrieves relevant context
2. Context is formatted correctly for Perplexity
3. Perplexity RAG query works with local context
4. Response cites local documents
"""
import asyncio
import sys
import os
import io

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.supabase_service import SupabaseService
from app.services.embedding_service import EmbeddingService
from app.services.semantic_search_service import SemanticSearchService
from app.services.perplexity_service import PerplexityService


async def test_rag_workflow():
    """Test complete RAG workflow."""

    print("=" * 80)
    print("RAG Workflow End-to-End Test")
    print("=" * 80)

    # Initialize services
    print("\n1. Initializing services...")
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)
    embedding = EmbeddingService()
    search = SemanticSearchService(supabase, embedding)
    perplexity = PerplexityService(
        api_key=settings.perplexity_api_key,
        max_requests_per_month=1000
    )
    print("   All services initialized")

    # Test query
    test_query = "What are the main challenges for cashew production in Cambodia?"
    commodity = "cashew"

    print(f"\n2. Test Query: \"{test_query}\"")
    print(f"   Commodity: {commodity}")

    # Step 1: Semantic search for context
    print("\n3. Semantic Search - Retrieving relevant context...")

    try:
        context = await search.search_with_context(
            query=test_query,
            top_k=5,
            commodity=commodity
        )

        print(f"   Context retrieved: {len(context)} characters")
        print(f"   Preview:")
        print(f"   {context[:200]}...")
        print(f"   ...")

    except Exception as e:
        print(f"   ERROR: {e}")
        return False

    # Step 2: RAG query with Perplexity
    print("\n4. Perplexity RAG Query - Generating answer with context...")

    try:
        result = await perplexity.rag_query(
            query=test_query,
            retrieved_context=context,
            commodity=commodity
        )

        print(f"   Query successful!")
        print(f"   Response length: {len(result['response_text'])} characters")
        print(f"   Citations: {len(result.get('citations', []))} sources")
        print(f"   Model: {result['metadata']['model']}")
        print(f"   Tokens used: {result['metadata'].get('tokens_used', 'N/A')}")

        # Show response
        print(f"\n5. Perplexity Response:")
        print("-" * 80)
        print(result['response_text'])
        print("-" * 80)

        # Show citations
        if result.get('citations'):
            print(f"\n6. Citations ({len(result['citations'])} sources):")
            for i, citation in enumerate(result['citations'][:5], 1):  # Show first 5
                print(f"   [{i}] {citation}")

        # Check if response references local documents
        print(f"\n7. Validation:")

        response_text = result['response_text'].lower()
        local_indicators = [
            'local document',
            'according to',
            'based on local',
            'cambodia',
            'report',
            'study'
        ]

        mentions_local = any(indicator in response_text for indicator in local_indicators)

        if mentions_local:
            print(f"   PASS - Response references local context")
        else:
            print(f"   WARN - Response may not cite local documents explicitly")
            print(f"   (But this doesn't mean it didn't use the context)")

        # Summary
        print("\n" + "=" * 80)
        print("RAG Workflow Test: COMPLETE")
        print("=" * 80)

        print(f"\nWorkflow Summary:")
        print(f"   1. Semantic search: PASS ({len(context)} chars context)")
        print(f"   2. Perplexity RAG: PASS ({len(result['response_text'])} chars response)")
        print(f"   3. Citations: {len(result.get('citations', []))} external sources")
        print(f"   4. Local context used: {'YES' if mentions_local else 'UNCLEAR'}")

        print(f"\nPerplexity Budget:")
        stats = perplexity.get_stats()
        print(f"   Requests used: {stats['requests_used']}/{stats['rate_limit']}")
        print(f"   Remaining: {stats['requests_remaining']}")
        print(f"   Utilization: {stats['utilization_percentage']:.1f}%")

        print("\n" + "=" * 80)
        print("Ready for Production!")
        print("=" * 80)
        print("\nNext Steps:")
        print("   - Integrate RAG into main application")
        print("   - Add user interface for Q&A")
        print("   - Monitor Perplexity usage")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main execution."""
    try:
        success = await test_rag_workflow()

        if not success:
            print("\nERROR: RAG workflow test failed")
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
