-- Migration: Add news articles and tweet count to market_trends table
-- Date: 2025-12-27
-- Purpose: Support comprehensive market analysis with news articles + improved tweet tracking

-- Add new columns for news articles
ALTER TABLE market_trends
ADD COLUMN IF NOT EXISTS news_articles JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS news_summary TEXT DEFAULT '',
ADD COLUMN IF NOT EXISTS tweet_count INTEGER DEFAULT 0;

-- Add comments for documentation
COMMENT ON COLUMN market_trends.news_articles IS 'Array of news articles with headline, source, date, url';
COMMENT ON COLUMN market_trends.news_summary IS 'Summary of news articles analysis';
COMMENT ON COLUMN market_trends.tweet_count IS 'Number of tweets found for this analysis';

-- Create index for faster queries on news articles
CREATE INDEX IF NOT EXISTS idx_market_trends_tweet_count ON market_trends(tweet_count);

-- Example data structure for news_articles:
-- [
--   {
--     "headline": "Cambodia exports 12 tonnes of cashew to Jordan",
--     "source": "Khmer Times",
--     "date": "Dec 20, 2025",
--     "url": "https://www.khmertimeskh.com/..."
--   }
-- ]
