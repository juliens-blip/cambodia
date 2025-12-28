-- Delete old trend analyses for cashew and rubber (2025-12-27)
-- This allows new analyses with tweets to be saved

DELETE FROM market_trends
WHERE trend_date = '2025-12-27'
AND commodity IN ('cashew', 'rubber');

-- Verify deletion
SELECT commodity, trend_date, twitter_sentiment, tweet_count
FROM market_trends
WHERE commodity IN ('cashew', 'rubber')
ORDER BY trend_date DESC
LIMIT 5;
