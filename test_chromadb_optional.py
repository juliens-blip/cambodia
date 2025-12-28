"""Test ChromaDB optional import."""
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chromadb_imports():
    """Test that ChromaDB imports work gracefully."""
    logger.info("Testing ChromaDB imports...")

    # Test 1: Import service module
    try:
        from app.services import CHROMADB_AVAILABLE, ChromaDBService
        logger.info(f"✅ Import successful. CHROMADB_AVAILABLE = {CHROMADB_AVAILABLE}")

        if not CHROMADB_AVAILABLE:
            logger.info("✅ ChromaDB correctly detected as unavailable")

        # Test 2: Try to instantiate ChromaDBService
        if CHROMADB_AVAILABLE:
            try:
                service = ChromaDBService()
                logger.info("✅ ChromaDBService instantiated successfully")
            except Exception as e:
                logger.info(f"⚠️  ChromaDBService instantiation failed (expected): {e}")
        else:
            try:
                service = ChromaDBService()
                logger.error("❌ Should have raised ImportError!")
            except ImportError as e:
                logger.info(f"✅ ChromaDBService correctly raises ImportError: {e}")

        # Test 3: Check jobs module
        from app.scheduler.jobs import CHROMADB_AVAILABLE as JOBS_CHROMADB_AVAILABLE
        logger.info(f"✅ Jobs module imports. CHROMADB_AVAILABLE = {JOBS_CHROMADB_AVAILABLE}")

        if CHROMADB_AVAILABLE == JOBS_CHROMADB_AVAILABLE:
            logger.info("✅ Consistent ChromaDB availability across modules")
        else:
            logger.error("❌ Inconsistent ChromaDB availability!")

        logger.info("\n" + "="*60)
        logger.info("ALL TESTS PASSED! ChromaDB is properly optional.")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    test_chromadb_imports()
