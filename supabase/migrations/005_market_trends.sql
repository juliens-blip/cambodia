-- Migration 005: Market Trends Monitoring (Twitter/X + Stock Data)
-- Created: 2024-12-27
-- Purpose: Track daily market sentiment from Twitter/X and stock market data

-- =====================================================
-- 1. MARKET TRENDS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS public.market_trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commodity VARCHAR(50) NOT NULL,
    trend_date DATE NOT NULL,

    -- Twitter/X Analysis
    twitter_sentiment VARCHAR(50),  -- 'bullish', 'bearish', 'neutral'
    twitter_volume INTEGER DEFAULT 0,
    twitter_summary TEXT,
    top_tweets JSONB DEFAULT '[]'::jsonb,

    -- Stock Market Data
    stock_price_usd DECIMAL(10, 2),
    stock_change_pct DECIMAL(5, 2),
    stock_volume BIGINT,
    market_summary TEXT,

    -- Combined Analysis
    overall_trend VARCHAR(50),  -- 'strong_bullish', 'bullish', 'neutral', 'bearish', 'strong_bearish'
    confidence_score DECIMAL(3, 2),  -- 0.00 to 1.00
    ai_analysis TEXT,
    key_factors JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    data_sources JSONB DEFAULT '[]'::jsonb,
    perplexity_citations JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint: one analysis per commodity per day
    CONSTRAINT unique_commodity_date UNIQUE (commodity, trend_date)
);

-- Index for date range queries
CREATE INDEX IF NOT EXISTS idx_market_trends_date
    ON public.market_trends(trend_date DESC);

-- Index for commodity filtering
CREATE INDEX IF NOT EXISTS idx_market_trends_commodity
    ON public.market_trends(commodity, trend_date DESC);

-- Index for sentiment analysis
CREATE INDEX IF NOT EXISTS idx_market_trends_sentiment
    ON public.market_trends(overall_trend, trend_date DESC);


-- =====================================================
-- 2. TREND ALERTS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS public.trend_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commodity VARCHAR(50) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,  -- 'price_spike', 'sentiment_shift', 'volume_surge'
    severity VARCHAR(20) NOT NULL,  -- 'low', 'medium', 'high', 'critical'
    message TEXT NOT NULL,
    trigger_data JSONB DEFAULT '{}'::jsonb,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for unread alerts
CREATE INDEX IF NOT EXISTS idx_trend_alerts_unread
    ON public.trend_alerts(is_read, created_at DESC);


-- =====================================================
-- 3. VIEWS FOR TREND ANALYSIS
-- =====================================================

-- Latest trends per commodity
CREATE OR REPLACE VIEW public.latest_trends AS
SELECT DISTINCT ON (commodity)
    commodity,
    trend_date,
    twitter_sentiment,
    stock_change_pct,
    overall_trend,
    confidence_score,
    ai_analysis,
    created_at
FROM public.market_trends
ORDER BY commodity, trend_date DESC;

-- Trend history (last 30 days)
CREATE OR REPLACE VIEW public.trend_history AS
SELECT
    commodity,
    trend_date,
    overall_trend,
    confidence_score,
    twitter_sentiment,
    stock_change_pct
FROM public.market_trends
WHERE trend_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY commodity, trend_date DESC;

-- Sentiment summary
CREATE OR REPLACE VIEW public.sentiment_summary AS
SELECT
    commodity,
    COUNT(*) as total_days,
    COUNT(*) FILTER (WHERE twitter_sentiment = 'bullish') as bullish_days,
    COUNT(*) FILTER (WHERE twitter_sentiment = 'bearish') as bearish_days,
    COUNT(*) FILTER (WHERE twitter_sentiment = 'neutral') as neutral_days,
    ROUND(AVG(confidence_score), 2) as avg_confidence,
    MAX(trend_date) as last_update
FROM public.market_trends
WHERE trend_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY commodity;


-- =====================================================
-- 4. FUNCTIONS
-- =====================================================

-- Get latest trend for a commodity
CREATE OR REPLACE FUNCTION get_latest_trend(p_commodity VARCHAR)
RETURNS TABLE (
    commodity VARCHAR,
    trend_date DATE,
    twitter_sentiment VARCHAR,
    stock_change_pct DECIMAL,
    overall_trend VARCHAR,
    confidence_score DECIMAL,
    ai_analysis TEXT,
    key_factors JSONB
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        mt.commodity,
        mt.trend_date,
        mt.twitter_sentiment,
        mt.stock_change_pct,
        mt.overall_trend,
        mt.confidence_score,
        mt.ai_analysis,
        mt.key_factors
    FROM public.market_trends mt
    WHERE mt.commodity = p_commodity
    ORDER BY mt.trend_date DESC
    LIMIT 1;
END;
$$;

-- Create alert if significant change detected
CREATE OR REPLACE FUNCTION create_trend_alert(
    p_commodity VARCHAR,
    p_alert_type VARCHAR,
    p_severity VARCHAR,
    p_message TEXT,
    p_trigger_data JSONB
)
RETURNS UUID
LANGUAGE plpgsql AS $$
DECLARE
    alert_id UUID;
BEGIN
    INSERT INTO public.trend_alerts (
        commodity,
        alert_type,
        severity,
        message,
        trigger_data
    ) VALUES (
        p_commodity,
        p_alert_type,
        p_severity,
        p_message,
        p_trigger_data
    )
    RETURNING id INTO alert_id;

    RETURN alert_id;
END;
$$;

-- Get unread alerts
CREATE OR REPLACE FUNCTION get_unread_alerts()
RETURNS TABLE (
    id UUID,
    commodity VARCHAR,
    alert_type VARCHAR,
    severity VARCHAR,
    message TEXT,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        ta.id,
        ta.commodity,
        ta.alert_type,
        ta.severity,
        ta.message,
        ta.created_at
    FROM public.trend_alerts ta
    WHERE ta.is_read = false
    ORDER BY ta.created_at DESC
    LIMIT 50;
END;
$$;


-- =====================================================
-- 5. TRIGGER FOR ALERT GENERATION
-- =====================================================

CREATE OR REPLACE FUNCTION auto_generate_alerts()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    -- Alert on strong price movement (>5%)
    IF ABS(NEW.stock_change_pct) > 5 THEN
        PERFORM create_trend_alert(
            NEW.commodity,
            'price_spike',
            CASE
                WHEN ABS(NEW.stock_change_pct) > 10 THEN 'critical'
                WHEN ABS(NEW.stock_change_pct) > 7 THEN 'high'
                ELSE 'medium'
            END,
            FORMAT('%s price changed by %s%% on %s',
                   NEW.commodity,
                   NEW.stock_change_pct,
                   NEW.trend_date),
            jsonb_build_object(
                'change_pct', NEW.stock_change_pct,
                'date', NEW.trend_date
            )
        );
    END IF;

    -- Alert on sentiment shift to bearish
    IF NEW.twitter_sentiment = 'bearish' AND NEW.confidence_score > 0.7 THEN
        PERFORM create_trend_alert(
            NEW.commodity,
            'sentiment_shift',
            'high',
            FORMAT('%s sentiment turned bearish (confidence: %s)',
                   NEW.commodity,
                   NEW.confidence_score),
            jsonb_build_object(
                'sentiment', NEW.twitter_sentiment,
                'confidence', NEW.confidence_score
            )
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trigger_auto_alerts
    AFTER INSERT ON public.market_trends
    FOR EACH ROW
    EXECUTE FUNCTION auto_generate_alerts();


-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration 005 complete - Market trends monitoring ready!';
    RAISE NOTICE 'Tables: market_trends, trend_alerts';
    RAISE NOTICE 'Views: latest_trends, trend_history, sentiment_summary';
    RAISE NOTICE 'Functions: get_latest_trend, create_trend_alert, get_unread_alerts';
    RAISE NOTICE 'Trigger: auto_generate_alerts (price spikes + sentiment shifts)';
END $$;
