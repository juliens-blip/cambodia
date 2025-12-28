-- Migration 004: Conversation History & Usage Tracking
-- Created: 2024-12-27
-- Purpose: Add tables for conversation history and usage monitoring

-- =====================================================
-- 1. CONVERSATION HISTORY TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS public.conversation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    user_query TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    query_type VARCHAR(50) NOT NULL, -- 'search' or 'rag'
    commodity VARCHAR(50),
    context_chunks_used INTEGER DEFAULT 0,
    similarity_score FLOAT,
    tokens_used INTEGER,
    execution_time_ms FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast session lookup
CREATE INDEX IF NOT EXISTS idx_conversation_session
    ON public.conversation_history(session_id, created_at DESC);

-- Index for query type filtering
CREATE INDEX IF NOT EXISTS idx_conversation_type
    ON public.conversation_history(query_type);

-- Index for commodity filtering
CREATE INDEX IF NOT EXISTS idx_conversation_commodity
    ON public.conversation_history(commodity);


-- =====================================================
-- 2. USAGE LOGS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS public.usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    query_type VARCHAR(50) NOT NULL, -- 'search', 'rag', 'history', 'stats'
    cost_usd DECIMAL(10, 6) DEFAULT 0.0,
    cached BOOLEAN DEFAULT false,
    status VARCHAR(50) DEFAULT 'success', -- 'success', 'error', 'rate_limited'
    error_message TEXT,
    execution_time_ms FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for date range queries
CREATE INDEX IF NOT EXISTS idx_usage_logs_date
    ON public.usage_logs(created_at DESC);

-- Index for session analysis
CREATE INDEX IF NOT EXISTS idx_usage_logs_session
    ON public.usage_logs(session_id);

-- Index for cost tracking
CREATE INDEX IF NOT EXISTS idx_usage_logs_cost
    ON public.usage_logs(cost_usd, created_at);


-- =====================================================
-- 3. CACHE TABLE (for Redis alternative)
-- =====================================================

CREATE TABLE IF NOT EXISTS public.query_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    response TEXT NOT NULL,
    context_used TEXT,
    citations JSONB,
    metadata JSONB DEFAULT '{}'::jsonb,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '24 hours')
);

-- Index for cache lookup
CREATE INDEX IF NOT EXISTS idx_query_cache_hash
    ON public.query_cache(query_hash);

-- Index for expiration cleanup
CREATE INDEX IF NOT EXISTS idx_query_cache_expires
    ON public.query_cache(expires_at);


-- =====================================================
-- 4. BUDGET TRACKING VIEW
-- =====================================================

CREATE OR REPLACE VIEW public.budget_tracking AS
SELECT
    DATE_TRUNC('month', created_at) AS month,
    DATE_TRUNC('day', created_at) AS day,
    COUNT(*) AS total_queries,
    COUNT(*) FILTER (WHERE query_type = 'search') AS search_queries,
    COUNT(*) FILTER (WHERE query_type = 'rag') AS rag_queries,
    COUNT(*) FILTER (WHERE cached = true) AS cached_queries,
    ROUND(
        COUNT(*) FILTER (WHERE cached = true)::DECIMAL / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS cache_hit_rate_pct,
    SUM(cost_usd) AS total_cost_usd,
    SUM(cost_usd) FILTER (WHERE query_type = 'rag') AS rag_cost_usd
FROM public.usage_logs
GROUP BY DATE_TRUNC('month', created_at), DATE_TRUNC('day', created_at)
ORDER BY day DESC;


-- =====================================================
-- 5. CLEANUP FUNCTIONS
-- =====================================================

-- Function to delete expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER
LANGUAGE plpgsql AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.query_cache
    WHERE expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$;

-- Function to archive old usage logs (older than 90 days)
CREATE OR REPLACE FUNCTION archive_old_usage_logs()
RETURNS INTEGER
LANGUAGE plpgsql AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- In production, move to archive table instead of delete
    DELETE FROM public.usage_logs
    WHERE created_at < NOW() - INTERVAL '90 days';

    GET DIAGNOSTICS archived_count = ROW_COUNT;

    RETURN archived_count;
END;
$$;


-- =====================================================
-- 6. RLS (ROW LEVEL SECURITY) - Optional
-- =====================================================

-- Enable RLS on tables (uncomment if needed)
-- ALTER TABLE public.conversation_history ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.usage_logs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.query_cache ENABLE ROW LEVEL SECURITY;


-- =====================================================
-- 7. HELPER FUNCTIONS
-- =====================================================

-- Get current month budget stats
CREATE OR REPLACE FUNCTION get_current_month_budget()
RETURNS TABLE (
    month DATE,
    total_queries BIGINT,
    rag_queries BIGINT,
    total_cost_usd DECIMAL,
    budget_limit_usd DECIMAL,
    budget_remaining_usd DECIMAL,
    budget_utilization_pct DECIMAL
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        DATE_TRUNC('month', NOW())::DATE AS month,
        COUNT(*) AS total_queries,
        COUNT(*) FILTER (WHERE query_type = 'rag') AS rag_queries,
        COALESCE(SUM(cost_usd), 0) AS total_cost_usd,
        5.0::DECIMAL AS budget_limit_usd,
        (5.0 - COALESCE(SUM(cost_usd), 0))::DECIMAL AS budget_remaining_usd,
        ROUND((COALESCE(SUM(cost_usd), 0) / 5.0) * 100, 2) AS budget_utilization_pct
    FROM public.usage_logs
    WHERE DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW());
END;
$$;


-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration 004 complete - Conversation history and usage tracking ready!';
    RAISE NOTICE 'Tables created: conversation_history, usage_logs, query_cache';
    RAISE NOTICE 'Views created: budget_tracking';
    RAISE NOTICE 'Functions created: cleanup_expired_cache, archive_old_usage_logs, get_current_month_budget';
END $$;
