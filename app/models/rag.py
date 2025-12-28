"""Pydantic models for RAG API requests and responses."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class SearchRequest(BaseModel):
    """Semantic search request."""
    query: str = Field(..., description="Search query in any language")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    commodity: Optional[str] = Field(default=None, description="Filter by commodity (cashew, rubber)")
    source: Optional[str] = Field(default=None, description="Filter by source")


class SearchResult(BaseModel):
    """Single search result."""
    id: str
    document_id: str
    chunk_index: int
    chunk_text: str
    similarity: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """Semantic search response."""
    query: str
    results: List[SearchResult]
    count: int
    execution_time_ms: float


class RAGRequest(BaseModel):
    """RAG query request."""
    query: str = Field(..., description="Question in any language")
    commodity: Optional[str] = Field(default=None, description="Commodity context")
    top_k: int = Field(default=5, ge=1, le=10, description="Number of context chunks")
    use_cache: bool = Field(default=True, description="Use cached responses if available")


class RAGResponse(BaseModel):
    """RAG query response."""
    query: str
    answer: str
    citations: List[str]
    context_used: int
    model: str
    tokens_used: Optional[int]
    execution_time_ms: float
    cached: bool = False


class ConversationMessage(BaseModel):
    """Single conversation message."""
    role: str = Field(..., description="user or assistant")
    content: str
    timestamp: datetime


class ConversationHistoryRequest(BaseModel):
    """Request for conversation history."""
    session_id: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)


class ConversationHistoryResponse(BaseModel):
    """Conversation history response."""
    session_id: str
    messages: List[ConversationMessage]
    count: int


class UsageStats(BaseModel):
    """Usage statistics."""
    total_queries: int
    search_queries: int
    rag_queries: int
    cache_hits: int
    cache_hit_rate: float
    total_cost_usd: float
    current_month_queries: int
    current_month_cost_usd: float
    budget_remaining_usd: float
    budget_utilization_pct: float


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    services: Dict[str, str]
    version: str
