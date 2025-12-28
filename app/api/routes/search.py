"""Semantic search API routes using ChromaDB."""
from fastapi import APIRouter, HTTPException, Query, Request, Body
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()


class SearchQuery(BaseModel):
    """Search query model."""
    query: str
    collection: Optional[str] = None
    commodity: Optional[str] = None
    n_results: int = 5


@router.post("/")
async def search(
    request: Request,
    search_query: SearchQuery = Body(...)
):
    """
    Semantic search across ChromaDB collections.

    Args:
        search_query: Search parameters

    Returns:
        Search results from ChromaDB
    """
    try:
        chromadb = request.app.state.chromadb

        # Determine which collection to search
        if search_query.collection:
            # Search specific collection
            collection_name = search_query.collection

            if collection_name == "commodity_documents":
                results = await chromadb.search_documents(
                    query=search_query.query,
                    commodity=search_query.commodity,
                    n_results=search_query.n_results
                )
            elif collection_name == "perplexity_analyses":
                results = await chromadb.search_analyses(
                    query=search_query.query,
                    commodity=search_query.commodity,
                    n_results=search_query.n_results
                )
            elif collection_name == "claude_reports":
                results = await chromadb.search_reports(
                    query=search_query.query,
                    commodity=search_query.commodity,
                    n_results=search_query.n_results
                )
            elif collection_name == "commodity_prices":
                results = await chromadb.search_similar_prices(
                    query=search_query.query,
                    commodity=search_query.commodity,
                    n_results=search_query.n_results
                )
            elif collection_name == "production_data":
                results = await chromadb.search_production(
                    query=search_query.query,
                    commodity=search_query.commodity,
                    n_results=search_query.n_results
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid collection: {collection_name}"
                )

            return {
                "query": search_query.query,
                "collection": collection_name,
                "commodity": search_query.commodity,
                "count": len(results),
                "results": results
            }

        else:
            # Search all collections
            all_results = {}

            all_results["documents"] = await chromadb.search_documents(
                query=search_query.query,
                commodity=search_query.commodity,
                n_results=search_query.n_results
            )

            all_results["analyses"] = await chromadb.search_analyses(
                query=search_query.query,
                commodity=search_query.commodity,
                n_results=search_query.n_results
            )

            all_results["reports"] = await chromadb.search_reports(
                query=search_query.query,
                commodity=search_query.commodity,
                n_results=search_query.n_results
            )

            all_results["prices"] = await chromadb.search_similar_prices(
                query=search_query.query,
                commodity=search_query.commodity,
                n_results=search_query.n_results
            )

            all_results["production"] = await chromadb.search_production(
                query=search_query.query,
                commodity=search_query.commodity,
                n_results=search_query.n_results
            )

            return {
                "query": search_query.query,
                "commodity": search_query.commodity,
                "collections": all_results
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def search_documents(
    request: Request,
    query: str = Query(..., description="Search query"),
    commodity: Optional[str] = Query(None, description="Filter by commodity"),
    n_results: int = Query(5, ge=1, le=20)
):
    """Search commodity documents (PDFs/KML)."""
    try:
        chromadb = request.app.state.chromadb

        results = await chromadb.search_documents(
            query=query,
            commodity=commodity,
            n_results=n_results
        )

        return {
            "query": query,
            "commodity": commodity,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar-prices")
async def search_similar_prices(
    request: Request,
    query: str = Query(..., description="Describe price scenario"),
    commodity: Optional[str] = Query(None, description="Filter by commodity"),
    n_results: int = Query(10, ge=1, le=50)
):
    """Find similar price scenarios."""
    try:
        chromadb = request.app.state.chromadb

        results = await chromadb.search_similar_prices(
            query=query,
            commodity=commodity,
            n_results=n_results
        )

        return {
            "query": query,
            "commodity": commodity,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections")
async def get_collections_info(request: Request):
    """Get information about available search collections."""
    chromadb = request.app.state.chromadb
    stats = chromadb.get_collection_stats()

    return {
        "collections": [
            {
                "name": "commodity_documents",
                "description": "PDF and KML documents from Google Drive",
                "count": stats.get("commodity_documents", {}).get("count", 0)
            },
            {
                "name": "perplexity_analyses",
                "description": "Perplexity API research results",
                "count": stats.get("perplexity_analyses", {}).get("count", 0)
            },
            {
                "name": "claude_reports",
                "description": "Generated market reports",
                "count": stats.get("claude_reports", {}).get("count", 0)
            },
            {
                "name": "commodity_prices",
                "description": "Price data with market context",
                "count": stats.get("commodity_prices", {}).get("count", 0)
            },
            {
                "name": "production_data",
                "description": "Production statistics with geospatial data",
                "count": stats.get("production_data", {}).get("count", 0)
            }
        ]
    }
