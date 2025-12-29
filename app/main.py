"""FastAPI main application for Cambodia Agri Analytics."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Configure logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from app.config import settings
from app.api.routes import prices, production, reports, search, quality
from app.services import ChromaDBService, SupabaseService
from app.middleware.rate_limiter import RateLimiter, RateLimitMiddleware

# Optional routes (require heavy dependencies like sentence-transformers)
SEMANTIC_AVAILABLE = False
TRENDS_AVAILABLE = False

# Try to import semantic routes (requires sentence-transformers)
try:
    from app.api.routes import semantic
    SEMANTIC_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Semantic routes not available: {e}")
    logger.info("ℹ️ The API will work without semantic search features")
    semantic = None

# Try to import trends routes (doesn't require sentence-transformers)
try:
    from app.api.routes import trends
    TRENDS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Trends routes not available: {e}")
    trends = None


# Global service instances
chromadb_service: ChromaDBService = None
supabase_service: SupabaseService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    logger.info("🚀 Starting Cambodia Agri Analytics API...")

    global chromadb_service, supabase_service

    # Initialize services
    # Try ChromaDB (optional - not needed for Phase 4)
    try:
        chromadb_service = ChromaDBService(
            host=settings.chroma_host,
            port=settings.chroma_port,
            persist_path=settings.chroma_persist_path
        )
        chromadb_service.init_collections()
        logger.info("✅ ChromaDB initialized")
    except ImportError as e:
        logger.warning(f"⚠️ ChromaDB not available (Python 3.14+ compatibility): {e}")
        logger.info("ℹ️ Continuing without ChromaDB - Phase 4 features will use Supabase pgvector")
        chromadb_service = None
    except Exception as e:
        logger.warning(f"⚠️ ChromaDB initialization failed: {e}")
        logger.info("ℹ️ Continuing without ChromaDB")
        chromadb_service = None

    # Initialize Supabase (optional for healthcheck to pass)
    try:
        supabase_service = SupabaseService(
            url=settings.supabase_url,
            key=settings.supabase_key
        )
        logger.info("✅ Supabase initialized")
    except Exception as e:
        logger.warning(f"⚠️ Supabase initialization failed: {e}")
        logger.info("ℹ️ API will start but database features may not work")
        supabase_service = None

    # Pre-load embedding model in background thread (takes 30-60s on Railway)
    # This prevents blocking the API startup while still pre-loading
    if SEMANTIC_AVAILABLE:
        import threading

        def load_embedding_model():
            try:
                logger.info("🔄 Pre-loading embedding model in background (this may take 30-60s)...")
                from app.services.embedding_service import get_embedding_service
                embedding_service = get_embedding_service()
                logger.info(f"✅ Embedding model loaded: {embedding_service.dimension} dimensions")
                app.state.embedding_service = embedding_service
            except Exception as e:
                logger.error(f"❌ Failed to load embedding model: {e}")
                app.state.embedding_service = None

        # Start loading in background thread
        embedding_thread = threading.Thread(target=load_embedding_model, daemon=True)
        embedding_thread.start()
        app.state.embedding_thread = embedding_thread
        logger.info("ℹ️ Embedding model loading started in background")
    else:
        app.state.embedding_service = None

    # Store services in app state
    app.state.chromadb = chromadb_service
    app.state.supabase = supabase_service

    logger.info("✅ API startup complete")

    yield

    # Shutdown
    logger.info("👋 Shutting down API...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Multi-commodity analytics platform for Cashew and Rubber markets in Cambodia",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure rate limiting (increased for development)
rate_limiter = RateLimiter(
    hourly_limit=50,   # 50 queries per hour per session (was 5)
    daily_limit=200,   # 200 queries per day total (was 50)
    monthly_limit=1000 # 1000 queries per month total
)
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

# Include routers
app.include_router(prices.router, prefix="/api/prices", tags=["Prices"])
app.include_router(production.router, prefix="/api/production", tags=["Production"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(quality.router, prefix="/api", tags=["Data Quality"])

# Optional routers (only if dependencies available)
if SEMANTIC_AVAILABLE:
    app.include_router(semantic.router, tags=["Semantic Search & RAG"])
    logger.info("✅ Semantic routes enabled")
else:
    logger.info("ℹ️ Semantic routes disabled (missing dependencies)")

if TRENDS_AVAILABLE:
    app.include_router(trends.router, tags=["Market Trends"])
    logger.info("✅ Trends routes enabled")
else:
    logger.info("ℹ️ Trends routes disabled (missing dependencies)")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Cambodia Agri Analytics API",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "running",
        "features": {
            "semantic_search": SEMANTIC_AVAILABLE,
            "market_trends": TRENDS_AVAILABLE
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint - simplified for Railway.

    Returns 200 OK if the app is running, regardless of database status.
    This ensures Railway healthcheck passes during startup.
    """
    return {"status": "ok"}


@app.get("/debug/embedding")
async def debug_embedding():
    """Debug endpoint to test embedding model loading."""
    result = {
        "semantic_available": SEMANTIC_AVAILABLE,
        "embedding_status": "not_tested",
        "embedding_dimension": None,
        "model_name": None,
        "error": None
    }

    if not SEMANTIC_AVAILABLE:
        result["error"] = "Semantic routes not available (missing sentence-transformers)"
        return result

    try:
        from app.services.embedding_service import get_embedding_service
        service = get_embedding_service()
        info = service.get_model_info()
        result["embedding_status"] = "ok"
        result["embedding_dimension"] = info.get("dimension")
        result["model_name"] = info.get("model_name")
    except Exception as e:
        result["embedding_status"] = "error"
        result["error"] = str(e)
        logger.error(f"Embedding debug error: {e}")

    return result


@app.get("/health/detailed")
async def health_check_detailed():
    """Detailed health check with service status."""
    try:
        # Check ChromaDB (optional)
        if hasattr(app.state, 'chromadb') and app.state.chromadb:
            chroma_stats = app.state.chromadb.get_collection_stats()
            chromadb_status = {
                "status": "up",
                "collections": len(chroma_stats)
            }
        else:
            chromadb_status = {
                "status": "unavailable",
                "message": "ChromaDB not installed"
            }

        # Check Supabase (optional)
        if hasattr(app.state, 'supabase') and app.state.supabase:
            db_stats = await app.state.supabase.get_database_stats()
            supabase_status = {
                "status": "up",
                "tables": len(db_stats)
            }
        else:
            supabase_status = {
                "status": "unavailable",
                "message": "Supabase not configured"
            }

        return {
            "status": "healthy",
            "services": {
                "chromadb": chromadb_status,
                "supabase": supabase_status
            }
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "status": "degraded",
            "error": str(e)
        }


@app.get("/stats")
async def get_stats():
    """Get database and collection statistics."""
    chroma_stats = app.state.chromadb.get_collection_stats() if app.state.chromadb else {}
    db_stats = await app.state.supabase.get_database_stats()

    return {
        "chromadb": chroma_stats,
        "supabase": db_stats
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.debug else False
    )
