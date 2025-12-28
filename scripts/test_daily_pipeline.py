"""
Test script for daily_pipeline - Cambodia Agri Analytics

This script tests the daily data collection and analysis pipeline
in both MOCK and REAL API modes.

Usage:
    # MOCK mode (default, no API costs)
    python scripts/test_daily_pipeline.py

    # Real API mode (uses actual Perplexity credits)
    python scripts/test_daily_pipeline.py --real

    # Dry run (check services only, no pipeline execution)
    python scripts/test_daily_pipeline.py --dry-run

    # Skip collectors (test only analysis generation)
    python scripts/test_daily_pipeline.py --skip-collectors
"""

import asyncio
import logging
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any

# Fix encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    sys.stderr.reconfigure(encoding='utf-8', errors='ignore')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings
from app.services import (
    PerplexityService,
    ClaudeMockService,
    ChromaDBService,
    SupabaseService
)
from app.scheduler.jobs import daily_pipeline, init_services

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f'logs/test_daily_pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            encoding='utf-8'
        )
    ]
)

logger = logging.getLogger(__name__)


class PipelineTester:
    """Test harness for daily_pipeline."""

    def __init__(self, mock_mode: bool = True, skip_collectors: bool = False):
        """
        Initialize pipeline tester.

        Args:
            mock_mode: If True, use MOCK mode for all services
            skip_collectors: If True, skip data collection step
        """
        self.mock_mode = mock_mode
        self.skip_collectors = skip_collectors
        self.supabase = None
        self.chromadb = None
        self.perplexity = None
        self.claude = None

    async def check_services(self) -> Dict[str, bool]:
        """
        Check that all required services are available.

        Returns:
            Dict with service names and their availability status
        """
        logger.info("=" * 80)
        logger.info("CHECKING SERVICES")
        logger.info("=" * 80)

        status = {}

        # Check Supabase
        try:
            self.supabase = SupabaseService(
                url=settings.supabase_url,
                key=settings.supabase_key
            )
            stats = await self.supabase.get_database_stats()
            logger.info(f"✅ Supabase connected - Database stats: {stats}")
            status["supabase"] = True
        except Exception as e:
            logger.error(f"❌ Supabase connection failed: {e}")
            status["supabase"] = False

        # Check ChromaDB (OPTIONAL - gracefully handle if unavailable)
        try:
            self.chromadb = ChromaDBService(
                host=settings.chroma_host,
                port=settings.chroma_port,
                persist_path=settings.chroma_persist_path
            )
            self.chromadb.init_collections()
            chroma_stats = self.chromadb.get_collection_stats()
            logger.info(f"✅ ChromaDB connected - Collections: {chroma_stats}")
            status["chromadb"] = True
        except Exception as e:
            logger.warning(f"⚠️  ChromaDB unavailable (OPTIONAL): {e}")
            logger.info("   Pipeline will continue without ChromaDB embeddings")
            status["chromadb"] = False
            self.chromadb = None  # Set to None to skip ChromaDB operations

        # Check Perplexity API
        try:
            if self.mock_mode:
                logger.info("ℹ️  Perplexity in MOCK mode - skipping API check")
                status["perplexity"] = True
            else:
                if not settings.perplexity_api_key or settings.perplexity_api_key == "":
                    raise ValueError("PERPLEXITY_API_KEY not configured in .env")

                self.perplexity = PerplexityService(
                    api_key=settings.perplexity_api_key,
                    max_requests_per_month=settings.perplexity_max_requests_per_month
                )
                logger.info(f"✅ Perplexity API key configured - {self.perplexity.get_stats()}")
                status["perplexity"] = True
        except Exception as e:
            logger.error(f"❌ Perplexity API check failed: {e}")
            status["perplexity"] = False

        # Check Claude (always MOCK for now)
        try:
            self.claude = ClaudeMockService(mock_mode=True)
            logger.info(f"✅ Claude service initialized (MOCK mode: {self.claude.mock_mode})")
            status["claude"] = True
        except Exception as e:
            logger.error(f"❌ Claude service failed: {e}")
            status["claude"] = False

        # Summary
        logger.info("\n" + "=" * 80)
        # Only require critical services (Supabase, Perplexity, Claude)
        # ChromaDB is optional
        critical_services = ["supabase", "perplexity", "claude"]
        critical_ok = all(status.get(svc, False) for svc in critical_services)

        if critical_ok:
            logger.info("✅ ALL CRITICAL SERVICES READY")
            if not status.get("chromadb", False):
                logger.info("   (ChromaDB unavailable but optional - will be skipped)")
        else:
            failed = [svc for svc in critical_services if not status.get(svc, False)]
            logger.error(f"❌ CRITICAL SERVICES UNAVAILABLE: {failed}")
        logger.info("=" * 80 + "\n")

        return status

    async def get_baseline_counts(self) -> Dict[str, int]:
        """Get current record counts before pipeline execution."""
        logger.info("=" * 80)
        logger.info("BASELINE COUNTS (BEFORE PIPELINE)")
        logger.info("=" * 80)

        # Supabase counts
        db_stats = await self.supabase.get_database_stats()
        logger.info(f"Supabase tables:")
        for table, count in db_stats.items():
            logger.info(f"  - {table}: {count} records")

        # ChromaDB counts (optional)
        chroma_stats = {}
        if self.chromadb:
            chroma_stats = self.chromadb.get_collection_stats()
            logger.info(f"\nChromaDB collections:")
            for name, info in chroma_stats.items():
                logger.info(f"  - {name}: {info['count']} documents")
        else:
            logger.info(f"\nChromaDB: Skipped (not available)")

        logger.info("=" * 80 + "\n")

        return {
            "supabase": db_stats,
            "chromadb": chroma_stats
        }

    async def run_pipeline_test(self) -> Dict[str, Any]:
        """
        Run the daily pipeline and collect results.

        Returns:
            Dict with test results and metrics
        """
        logger.info("=" * 80)
        logger.info(f"RUNNING DAILY PIPELINE TEST (MOCK={self.mock_mode})")
        logger.info("=" * 80)

        # Initialize services for jobs module
        init_services(self.supabase, self.chromadb)

        # Override Perplexity with mock if needed
        if self.mock_mode:
            logger.info("⚠️  MOCK MODE ENABLED - Using mock Perplexity responses")
            from app.scheduler import jobs
            jobs.perplexity = MockPerplexityService()

        start_time = datetime.now()

        try:
            # Run the pipeline
            await daily_pipeline()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info(f"✅ Pipeline completed in {duration:.2f} seconds")

            return {
                "success": True,
                "duration_seconds": duration,
                "error": None
            }

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.error(f"❌ Pipeline failed after {duration:.2f} seconds: {e}")
            logger.exception("Full traceback:")

            return {
                "success": False,
                "duration_seconds": duration,
                "error": str(e)
            }

    async def verify_results(self, baseline: Dict[str, int]) -> Dict[str, Any]:
        """
        Verify that pipeline generated expected data.

        Args:
            baseline: Baseline counts before pipeline

        Returns:
            Dict with verification results
        """
        logger.info("\n" + "=" * 80)
        logger.info("VERIFYING RESULTS (AFTER PIPELINE)")
        logger.info("=" * 80)

        # Get new counts
        db_stats = await self.supabase.get_database_stats()
        chroma_stats = self.chromadb.get_collection_stats() if self.chromadb else {}

        # Calculate deltas
        verification = {
            "supabase_changes": {},
            "chromadb_changes": {},
            "expected_analyses": 2,  # cashew + rubber
            "expected_reports": 2,   # cashew + rubber
            "all_checks_passed": True
        }

        logger.info("Supabase table changes:")
        for table, new_count in db_stats.items():
            old_count = baseline["supabase"].get(table, 0)
            delta = new_count - old_count
            verification["supabase_changes"][table] = delta

            icon = "✅" if delta > 0 else "➖"
            logger.info(f"  {icon} {table}: {old_count} → {new_count} (+{delta})")

        if self.chromadb:
            logger.info("\nChromaDB collection changes:")
            for name, info in chroma_stats.items():
                old_count = baseline["chromadb"].get(name, {}).get("count", 0)
                new_count = info["count"]
                delta = new_count - old_count
                verification["chromadb_changes"][name] = delta

                icon = "✅" if delta > 0 else "➖"
                logger.info(f"  {icon} {name}: {old_count} → {new_count} (+{delta})")
        else:
            logger.info("\nChromaDB: Skipped (not available)")

        # Check expectations
        logger.info("\nExpected results:")

        # Should have 2 new perplexity_analyses
        analyses_added = verification["supabase_changes"].get("perplexity_analyses", 0)
        if analyses_added >= 2:
            logger.info(f"  ✅ Perplexity analyses: {analyses_added} added (expected: 2)")
        else:
            logger.warning(f"  ❌ Perplexity analyses: {analyses_added} added (expected: 2)")
            verification["all_checks_passed"] = False

        # Should have 2 new claude_reports
        reports_added = verification["supabase_changes"].get("claude_reports", 0)
        if reports_added >= 2:
            logger.info(f"  ✅ Claude reports: {reports_added} added (expected: 2)")
        else:
            logger.warning(f"  ❌ Claude reports: {reports_added} added (expected: 2)")
            verification["all_checks_passed"] = False

        # ChromaDB should have matching additions (if available)
        if self.chromadb:
            chroma_analyses = verification["chromadb_changes"].get("perplexity_analyses", 0)
            chroma_reports = verification["chromadb_changes"].get("claude_reports", 0)

            if chroma_analyses >= 2 and chroma_reports >= 2:
                logger.info(f"  ✅ ChromaDB embeddings: {chroma_analyses} analyses, {chroma_reports} reports")
            else:
                logger.warning(f"  ❌ ChromaDB embeddings: {chroma_analyses} analyses, {chroma_reports} reports (expected: 2 each)")
                verification["all_checks_passed"] = False
        else:
            logger.info(f"  ⚠️  ChromaDB embeddings: Skipped (ChromaDB not available)")

        logger.info("=" * 80 + "\n")

        return verification

    async def display_sample_data(self) -> None:
        """Display sample generated data."""
        logger.info("=" * 80)
        logger.info("SAMPLE GENERATED DATA")
        logger.info("=" * 80)

        # Get commodities
        cashew = await self.supabase.get_or_create_commodity("cashew", "nut")
        rubber = await self.supabase.get_or_create_commodity("rubber", "latex")

        # Get latest analysis
        cashew_analyses = await self.supabase.get_recent_analyses(cashew["id"], limit=1)
        if cashew_analyses:
            analysis = cashew_analyses[0]
            logger.info("\n📊 Latest Cashew Analysis:")
            logger.info(f"  - Query Type: {analysis.get('query_type')}")
            logger.info(f"  - Created: {analysis.get('created_at')}")
            logger.info(f"  - Response: {analysis.get('response_text', '')[:200]}...")
            logger.info(f"  - Citations: {len(analysis.get('citations', []))} sources")

        # Get latest report
        cashew_reports = await self.supabase.get_reports(cashew["id"], limit=1)
        if cashew_reports:
            report = cashew_reports[0]
            logger.info("\n📄 Latest Cashew Report:")
            logger.info(f"  - Title: {report.get('title')}")
            logger.info(f"  - Type: {report.get('report_type')}")
            logger.info(f"  - Created: {report.get('created_at')}")
            logger.info(f"  - Content preview:\n{report.get('content', '')[:300]}...")

        logger.info("\n" + "=" * 80 + "\n")

    async def run_full_test(self) -> Dict[str, Any]:
        """
        Run complete pipeline test with all checks.

        Returns:
            Dict with complete test results
        """
        results = {
            "test_started_at": datetime.now().isoformat(),
            "mock_mode": self.mock_mode,
            "skip_collectors": self.skip_collectors
        }

        # 1. Check services
        service_status = await self.check_services()
        results["service_status"] = service_status

        # Only require critical services
        critical_services = ["supabase", "perplexity", "claude"]
        critical_ok = all(service_status.get(svc, False) for svc in critical_services)

        if not critical_ok:
            failed = [svc for svc in critical_services if not service_status.get(svc, False)]
            logger.error(f"❌ Cannot run pipeline - critical services unavailable: {failed}")
            results["test_completed"] = False
            return results

        # 2. Get baseline
        baseline = await self.get_baseline_counts()
        results["baseline"] = baseline

        # 3. Run pipeline
        pipeline_result = await self.run_pipeline_test()
        results["pipeline_execution"] = pipeline_result

        if not pipeline_result["success"]:
            logger.error("❌ Pipeline execution failed")
            results["test_completed"] = False
            return results

        # 4. Verify results
        verification = await self.verify_results(baseline)
        results["verification"] = verification

        # 5. Display samples
        await self.display_sample_data()

        # Final summary
        results["test_completed"] = True
        results["test_ended_at"] = datetime.now().isoformat()
        results["overall_success"] = verification["all_checks_passed"]

        logger.info("=" * 80)
        if results["overall_success"]:
            logger.info("✅ ALL TESTS PASSED")
        else:
            logger.warning("⚠️  SOME TESTS FAILED - Check logs above")
        logger.info("=" * 80)

        return results


class MockPerplexityService:
    """Mock Perplexity service for testing without API costs."""

    async def research_daily_prices(self, commodity: str) -> Dict[str, Any]:
        """Generate mock daily price analysis."""
        logger.info(f"🔄 MOCK: Generating daily price analysis for {commodity}")

        mock_response = f"""
## Current Market Analysis for {commodity.title()} in Cambodia

### Latest Export Prices
- Current price range: $2,800-3,200 USD per ton (FOB)
- Price trend: Stable with slight upward pressure (+2.3% week-over-week)
- Quality premium: Grade A commands 15-20% premium over Grade B

### Key Destination Countries
1. **Vietnam** (45% of exports): Processing hub for cashew kernels
2. **China** (30% of exports): Growing demand for premium grades
3. **Europe** (15% of exports): Organic and certified products
4. **Other markets** (10%): Japan, South Korea, Middle East

### Supply/Demand Dynamics
- **Supply**: Cambodia's harvest season (Feb-May) nearing end
- **Demand**: Strong demand from Vietnam processors continues
- **Competition**: Thailand and Indonesia offering competitive pricing
- **Quality**: Cambodian {commodity} maintains reputation for quality

### Geopolitical Factors
- US-China trade tensions creating opportunities for ASEAN exporters
- Vietnam processing capacity expansion driving regional demand
- Currency fluctuations: Riel stable against USD, supporting export margins
- Trade agreements: Cambodia-China FTA benefits continuing

### Quality Grade Impact
- Premium grades (A1, A2): 20-25% price premium
- Standard grades (B, C): Baseline pricing
- Quality certification (organic, fair trade): Additional 10-15% premium
- Processing standards: Meeting international standards crucial for EU market
"""

        return {
            "commodity": commodity,
            "query_type": "price",
            "query_text": f"Daily price analysis for {commodity}",
            "response_text": mock_response.strip(),
            "citations": [
                "https://example.com/market-data-1",
                "https://example.com/market-data-2"
            ],
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {
                "model": "MOCK",
                "tokens_used": 0,
                "request_id": "mock-request-" + datetime.now().strftime("%Y%m%d%H%M%S")
            }
        }


async def main():
    """Main test execution."""
    parser = argparse.ArgumentParser(description="Test daily_pipeline")
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use real Perplexity API (costs credits)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check services only, don't run pipeline"
    )
    parser.add_argument(
        "--skip-collectors",
        action="store_true",
        help="Skip data collection step"
    )

    args = parser.parse_args()

    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    # Create tester
    tester = PipelineTester(
        mock_mode=not args.real,
        skip_collectors=args.skip_collectors
    )

    if args.dry_run:
        logger.info("DRY RUN MODE - Checking services only")
        service_status = await tester.check_services()

        # Only require critical services
        critical_services = ["supabase", "perplexity", "claude"]
        critical_ok = all(service_status.get(svc, False) for svc in critical_services)

        if critical_ok:
            logger.info("✅ All critical services ready for pipeline execution")
            return 0
        else:
            failed = [svc for svc in critical_services if not service_status.get(svc, False)]
            logger.error(f"❌ Critical services not ready: {failed}")
            return 1

    # Run full test
    results = await tester.run_full_test()

    # Save results to file
    import json
    results_file = f"logs/pipeline_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"\n📁 Full results saved to: {results_file}")

    return 0 if results.get("overall_success") else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
