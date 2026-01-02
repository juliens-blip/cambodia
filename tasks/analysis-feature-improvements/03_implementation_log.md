# Implementation Log: Feature Analyse - Harmonisation Cashew/Rubber

Date: 2026-01-02

- Updated cashew price references to RCN 1,800–2,200 and kernels W320 6,200–6,800 across prompts, validations, and public price series.
- Added trend label resolution + sentiment scoring in `market_trends_service.py`, with cautious labels (slightly bullish/bearish) and tweet-count thresholds.
- Added configurable `RUBBER_FARMGATE_FACTOR` and propagated to backend/UI.
- Added cashew Cambodia metrics block in scenario analysis (RCN range, farmgate range, export revenue range, families affected).
- Updated Market Trends UI: new trend labels, sentiment “not enough data”, price basis display, and rubber snapshot tweaks.
- Added translations for new trend labels and tweet-volume/sentiment text.
- Added UI text postprocessing (ranges cleanup, split text collapse) and applied to Market Trends, Scenario Analysis, and AI Q&A outputs.
- Added FX reference captions (USD/KHR) and unit conversions (USD/kg, KHR/kg, cents/kg) in Market Trends and Scenario Analysis.
- Added Cambodia Cashew Snapshot block in Market Trends and compacted Twitter/News/Market/Synthesis sections.
- Standardized sentiment display with score + tweet count and neutral label without emoji.
