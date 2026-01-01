# Plan: Market Trends UI display fix

## Objective
Normalize character-split text in Market Trends UI without altering normal formatting.

## Steps
1. Add a helper in `ui/pages/5_Market_Trends.py` to collapse long runs of short lines (<=4 chars) into a single string while preserving blank-line paragraph breaks.
2. Apply the helper to `twitter_summary`, `top_tweets`, `key_factors`, and `ai_analysis` before calling `st.markdown`.
3. Log changes in `tasks/market-trends-display-fix/03_implementation_log.md`.
4. Commit and push; ask the user to redeploy on Railway and re-run the manual analysis.
