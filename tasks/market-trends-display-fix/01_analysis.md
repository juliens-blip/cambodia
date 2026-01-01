# Analysis: Market Trends UI display fix

## Context
Date: 2026-01-02
Request: Market Trends UI shows numbers/words split per character (e.g. 1\n,\n800\n/\nt\no\nn). Also verify daily trend date update behavior.

## Current state
- `ui/pages/5_Market_Trends.py` renders `twitter_summary`, `top_tweets`, `key_factors`, and `ai_analysis` directly via `st.markdown`.
- `app/services/market_trends_service.py` stores `ai_analysis` as the raw Perplexity response. No normalization is applied.
- Trend dates are computed with `_get_local_date()` using `settings.timezone` (Asia/Phnom_Penh) but this requires the latest code to be deployed.

## Likely cause
- The UI is displaying raw text that sometimes contains newline-separated characters (likely from upstream LLM output or serialization), causing per-character line breaks.

## Files in scope
- `ui/pages/5_Market_Trends.py` (display layer)
- `app/services/market_trends_service.py` (date logic already adjusted)

## Constraints
- Keep normal markdown formatting intact.
- Apply a conservative fix that only collapses obvious character-split artifacts.
