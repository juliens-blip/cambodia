"""ChromaDB service wrapper for semantic search."""
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    Settings = None

from typing import List, Dict, Any, Optional
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


class ChromaDBService:
    """
    Service wrapper for ChromaDB vector database.

    Manages 5 collections for semantic search:
    1. commodity_documents - PDFs/KML from Google Drive
    2. perplexity_analyses - Perplexity research results
    3. claude_reports - Generated reports
    4. commodity_prices - Prices with market context
    5. production_data - Production stats with geospatial
    """

    def __init__(self, host: str = "localhost", port: int = 8000, persist_path: str = "chroma_data"):
        """
        Initialize ChromaDB service.

        Args:
            host: ChromaDB server host
            port: ChromaDB server port
            persist_path: Local path for embedded storage fallback
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "ChromaDB is not installed. "
                "This is expected with Python 3.14+ (ChromaDB not yet compatible). "
                "The service will be skipped gracefully."
            )

        self.host = host
        self.port = port
        self.persist_path = persist_path
        self.use_http = True

        try:
            self.client = chromadb.HttpClient(host=host, port=port)
            self.client.heartbeat()
        except Exception as exc:
            logger.warning(f"ChromaDB server unavailable, using embedded storage: {exc}")
            self.client = chromadb.PersistentClient(path=persist_path)
            self.use_http = False
        self.collections = {}

        if self.use_http:
            logger.info(f"ChromaDB service initialized (http://{host}:{port})")
        else:
            logger.info(f"ChromaDB service initialized (embedded at {persist_path})")

    def init_collections(self) -> None:
        """Initialize all 5 collections if they don't exist."""
        collection_names = [
            "commodity_documents",
            "perplexity_analyses",
            "claude_reports",
            "commodity_prices",
            "production_data"
        ]

        for name in collection_names:
            try:
                collection = self.client.get_collection(name=name)
                logger.info(f"Collection '{name}' already exists")
            except Exception:
                collection = self.client.create_collection(
                    name=name,
                    metadata={"description": f"Collection for {name.replace('_', ' ')}"}
                )
                logger.info(f"Created collection '{name}'")

            self.collections[name] = collection

    # ========== COMMODITY DOCUMENTS ==========

    async def store_document(
        self,
        commodity: str,
        file_name: str,
        content: str,
        file_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store document in commodity_documents collection.

        Args:
            commodity: 'cashew' or 'rubber'
            file_name: Document filename
            content: Extracted text content
            file_type: 'pdf' or 'kml'
            metadata: Additional metadata

        Returns:
            Document ID
        """
        collection = self.collections["commodity_documents"]

        doc_id = str(uuid4())
        meta = {
            "commodity": commodity,
            "file_name": file_name,
            "file_type": file_type,
            **(metadata or {})
        }

        collection.add(
            documents=[content],
            metadatas=[meta],
            ids=[doc_id]
        )

        logger.info(f"Stored document: {file_name} ({commodity})")
        return doc_id

    async def search_documents(
        self,
        query: str,
        commodity: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search commodity documents.

        Args:
            query: Search query
            commodity: Filter by commodity (optional)
            n_results: Number of results

        Returns:
            List of matching documents
        """
        collection = self.collections["commodity_documents"]

        where_filter = {"commodity": commodity} if commodity else None

        results = collection.query(
            query_texts=[query],
            where=where_filter,
            n_results=n_results
        )

        return self._format_results(results)

    # ========== PERPLEXITY ANALYSES ==========

    async def store_analysis(self, analysis: Dict[str, Any]) -> str:
        """
        Store Perplexity analysis.

        Args:
            analysis: Analysis dict from PerplexityService

        Returns:
            Analysis ID
        """
        collection = self.collections["perplexity_analyses"]

        analysis_id = str(uuid4())

        collection.add(
            documents=[analysis["response_text"]],
            metadatas=[{
                "commodity": analysis["commodity"],
                "query_type": analysis["query_type"],
                "query_text": analysis["query_text"],
                "created_at": analysis["created_at"],
                "citations": str(analysis.get("citations", []))
            }],
            ids=[analysis_id]
        )

        logger.info(f"Stored Perplexity analysis: {analysis['commodity']} ({analysis['query_type']})")
        return analysis_id

    async def search_analyses(
        self,
        query: str,
        commodity: Optional[str] = None,
        query_type: Optional[str] = None,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """Search Perplexity analyses."""
        collection = self.collections["perplexity_analyses"]

        where_filter = {}
        if commodity:
            where_filter["commodity"] = commodity
        if query_type:
            where_filter["query_type"] = query_type

        results = collection.query(
            query_texts=[query],
            where=where_filter if where_filter else None,
            n_results=n_results
        )

        return self._format_results(results)

    # ========== CLAUDE REPORTS ==========

    async def store_report(self, report: Dict[str, Any]) -> str:
        """Store Claude report."""
        collection = self.collections["claude_reports"]

        report_id = str(uuid4())

        collection.add(
            documents=[report["content"]],
            metadatas=[{
                "commodity": report["commodity"],
                "report_type": report["report_type"],
                "title": report["title"],
                "created_at": report["created_at"],
                "insights": str(report.get("insights", [])),
                "recommendations": str(report.get("recommendations", []))
            }],
            ids=[report_id]
        )

        logger.info(f"Stored report: {report['title']}")
        return report_id

    async def search_reports(
        self,
        query: str,
        commodity: Optional[str] = None,
        report_type: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search Claude reports."""
        collection = self.collections["claude_reports"]

        where_filter = {}
        if commodity:
            where_filter["commodity"] = commodity
        if report_type:
            where_filter["report_type"] = report_type

        results = collection.query(
            query_texts=[query],
            where=where_filter if where_filter else None,
            n_results=n_results
        )

        return self._format_results(results)

    # ========== COMMODITY PRICES ==========

    async def store_price_with_context(
        self,
        commodity: str,
        date: str,
        price_usd: float,
        context: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store price with market context."""
        collection = self.collections["commodity_prices"]

        price_id = str(uuid4())

        meta = {
            "commodity": commodity,
            "date": date,
            "price_usd": price_usd,
            **(metadata or {})
        }

        collection.add(
            documents=[context],
            metadatas=[meta],
            ids=[price_id]
        )

        logger.info(f"Stored price context: {commodity} ${price_usd} on {date}")
        return price_id

    async def search_similar_prices(
        self,
        query: str,
        commodity: Optional[str] = None,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search similar price scenarios."""
        collection = self.collections["commodity_prices"]

        where_filter = {"commodity": commodity} if commodity else None

        results = collection.query(
            query_texts=[query],
            where=where_filter,
            n_results=n_results
        )

        return self._format_results(results)

    # ========== PRODUCTION DATA ==========

    async def store_production_context(
        self,
        commodity: str,
        year: int,
        province: str,
        context: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store production data with context."""
        collection = self.collections["production_data"]

        prod_id = str(uuid4())

        meta = {
            "commodity": commodity,
            "year": year,
            "province": province,
            **(metadata or {})
        }

        collection.add(
            documents=[context],
            metadatas=[meta],
            ids=[prod_id]
        )

        logger.info(f"Stored production context: {commodity} {province} {year}")
        return prod_id

    async def search_production(
        self,
        query: str,
        commodity: Optional[str] = None,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search production data."""
        collection = self.collections["production_data"]

        where_filter = {"commodity": commodity} if commodity else None

        results = collection.query(
            query_texts=[query],
            where=where_filter,
            n_results=n_results
        )

        return self._format_results(results)

    # ========== UTILITIES ==========

    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format ChromaDB query results."""
        formatted = []

        if not results.get("ids"):
            return formatted

        for i, doc_id in enumerate(results["ids"][0]):
            result = {
                "id": doc_id,
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else None
            }
            formatted.append(result)

        return formatted

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections."""
        stats = {}

        for name, collection in self.collections.items():
            count = collection.count()
            stats[name] = {
                "count": count,
                "name": name
            }

        return stats
