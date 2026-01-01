"""
Background Jobs with APScheduler
Daily market analysis for cambodian agricultural commodities
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime


# Create scheduler instance (will be started in main.py)
scheduler = AsyncIOScheduler()


async def daily_market_analysis():
    """
    Run daily market analysis for all commodities at 9:00 AM
    This job:
    1. Analyzes Twitter/X sentiment
    2. Fetches stock market data
    3. Generates AI analysis via Perplexity
    4. Stores results in Supabase
    """
    from app.services.market_trends_service import get_market_trends_service
    from app.main import get_supabase_client, get_perplexity_service

    print(f"[SCHEDULER] Starting daily market analysis at {datetime.now()}", flush=True)

    commodities = ["cashew", "rubber"]

    for commodity in commodities:
        try:
            print(f"[SCHEDULER] Analyzing {commodity}...", flush=True)

            # Get services
            supabase = get_supabase_client()
            perplexity = get_perplexity_service()
            trends_service = get_market_trends_service(supabase, perplexity)

            # Run analysis (force_refresh=True to ensure new analysis)
            result = await trends_service.analyze_and_store_trends(
                commodity=commodity,
                force_refresh=True
            )

            print(f"[SCHEDULER] ✅ {commodity} analysis completed: {result}", flush=True)

        except Exception as e:
            print(f"[SCHEDULER] ❌ Error analyzing {commodity}: {e}", flush=True)

    print(f"[SCHEDULER] Daily market analysis completed at {datetime.now()}", flush=True)


def schedule_daily_jobs():
    """Schedule all daily jobs"""

    # Daily market analysis at 9:00 AM (Cambodia time - UTC+7)
    # If Railway/server is UTC, this runs at 02:00 UTC = 09:00 Cambodia time
    scheduler.add_job(
        daily_market_analysis,
        trigger=CronTrigger(hour=2, minute=0),  # 02:00 UTC = 09:00 Cambodia
        id="daily_market_analysis",
        name="Daily Market Analysis (9:00 AM Cambodia)",
        replace_existing=True,
        max_instances=1,  # Prevent multiple concurrent runs
    )

    print("[SCHEDULER] Scheduled job: Daily Market Analysis at 02:00 UTC (09:00 Cambodia)", flush=True)


def start_scheduler():
    """Start the scheduler"""
    if not scheduler.running:
        schedule_daily_jobs()
        scheduler.start()
        print("[SCHEDULER] ✅ Scheduler started", flush=True)
    else:
        print("[SCHEDULER] ⚠️ Scheduler already running", flush=True)


def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    if scheduler.running:
        scheduler.shutdown(wait=True)
        print("[SCHEDULER] 🛑 Scheduler stopped", flush=True)
