"""Perplexity API service for market research."""
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PerplexityService:
    """Service for Perplexity API research queries."""

    def __init__(self, api_key: str, max_requests_per_month: int = 1000):
        """
        Initialize Perplexity service.

        Args:
            api_key: Perplexity API key
            max_requests_per_month: Rate limit (default 1000)
        """
        self.api_key = api_key
        self.max_requests = max_requests_per_month
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.request_count = 0

    async def research_daily_prices(self, commodity: str) -> Dict[str, Any]:
        """
        Research current market conditions for daily price analysis.

        Args:
            commodity: 'cashew' or 'rubber'

        Returns:
            Dict with response text and citations
        """
        prompt = f"""Analyze current market conditions for {commodity} in Cambodia:
1. Latest export prices (USD per ton)
2. Key destination countries (Vietnam, China, Europe)
3. Supply/demand dynamics
4. Geopolitical factors affecting trade
5. Quality grades impact on pricing

Focus on factual data from last 7 days. Include citations."""

        return await self._query(prompt, commodity, query_type="price")

    async def research_comprehensive(self, commodity: str) -> Dict[str, Any]:
        """
        Comprehensive market research for weekly deep dive.

        Args:
            commodity: 'cashew' or 'rubber'

        Returns:
            Dict with response text and citations
        """
        week_number = datetime.now().isocalendar()[1]

        prompt = f"""Comprehensive {commodity} market analysis for Cambodia (week {week_number}):
1. Price trend analysis (last 4 weeks)
2. Major geopolitical events impact
3. Regional competition (Vietnam, Thailand, Indonesia)
4. Processing industry updates
5. Future outlook (next 30 days)

Provide detailed citations and data sources."""

        return await self._query(prompt, commodity, query_type="market")

    async def research_geopolitics(
        self,
        commodity: str,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Research geopolitical events affecting commodity markets.

        Args:
            commodity: 'cashew' or 'rubber'
            topic: Optional specific topic (e.g., "US-China trade war")

        Returns:
            Dict with response text and citations
        """
        if topic:
            prompt = f"""Analyze geopolitical impact of {topic} on {commodity} trade in Cambodia:
1. Direct effects on Cambodia exports
2. Regional supply chain disruptions
3. Price impact analysis
4. Future outlook

Include recent news and citations."""
        else:
            prompt = f"""Recent geopolitical events affecting {commodity} trade in Cambodia:
1. Trade policy changes
2. Regional conflicts or disputes
3. Currency fluctuations
4. Export/import restrictions

Focus on last 30 days. Include citations."""

        return await self._query(prompt, commodity, query_type="geopolitics")

    async def rag_query(
        self,
        query: str,
        retrieved_context: str,
        commodity: str
    ) -> Dict[str, Any]:
        """
        RAG (Retrieval Augmented Generation) query with context from local documents.

        This method combines:
        1. Retrieved context from semantic search (local PDFs/documents)
        2. Perplexity online knowledge
        3. User query

        Use this for:
        - Q&A based on local document collection
        - Fact-checking against local sources
        - Combining internal + external knowledge

        Args:
            query: User question
            retrieved_context: Context chunks from semantic search (top 5 chunks formatted)
                              Format:
                              ```
                              [Source 1: GDrive - iTrade Bulletin]
                              Cashew production data...

                              ---

                              [Source 2: ODC - Report]
                              Province statistics...
                              ```
            commodity: 'cashew' or 'rubber'

        Returns:
            Dict with structure:
            {
                'commodity': str,
                'query_type': 'rag',
                'query_text': str (original user question),
                'response_text': str (Perplexity answer),
                'citations': List[str] (web sources),
                'created_at': str (ISO timestamp),
                'metadata': {
                    'model': str,
                    'tokens_used': int,
                    'request_id': str,
                    'context_length': int  # Length of local context provided
                }
            }

        Example:
            >>> # Step 1: Semantic search for context
            >>> context = await search.search_with_context(
            ...     "Cashew production Kampong Thom",
            ...     top_k=5,
            ...     commodity="cashew"
            ... )
            >>>
            >>> # Step 2: RAG query with context
            >>> result = await perplexity.rag_query(
            ...     query="What are cashew production statistics for Kampong Thom?",
            ...     retrieved_context=context,
            ...     commodity="cashew"
            ... )
            >>>
            >>> print(result['response_text'])
            "According to the iTrade Bulletin (local document), Kampong Thom
            produced 5,200 tons of cashew in 2023. This represents..."

        Performance:
            - Embedding + search: ~150ms (semantic_search_service)
            - Perplexity API call: ~2-5s (network + LLM)
            - Total: ~2-5s end-to-end

        Cost:
            - Semantic search: $0 (local + Supabase free tier)
            - Perplexity API: ~$0.005 per query
            - Total: ~$0.005 per RAG query

        Note:
            - Context is injected into prompt (prompt injection method)
            - Perplexity model: sonar-pro (2025)
            - Max context: 128k tokens (~500 pages)
            - Typical context: 5 chunks × 2k chars = 10k chars (~2.5k tokens)
        """
        # Build RAG prompt with context
        prompt = f"""You are an expert agricultural analyst for Cambodia specializing in {commodity}.

USE THE FOLLOWING LOCAL DOCUMENTS AS YOUR PRIMARY SOURCE:

{retrieved_context}

---

IMPORTANT INSTRUCTIONS:
1. Answer the question primarily based on the local documents above
2. If the local documents contain relevant information, cite them explicitly (e.g., "According to the iTrade Bulletin...")
3. If local documents are insufficient, supplement with your online knowledge BUT clearly distinguish:
   - "Based on local documents: ..."
   - "Based on external sources: ..."
4. Provide specific data, statistics, and facts
5. If conflicting information exists, mention both local and external sources
6. Focus on Cambodia-specific information about {commodity}

USER QUESTION: {query}

Answer:"""

        return await self._query(prompt, commodity, query_type="rag")

    async def _query(
        self,
        prompt: str,
        commodity: str,
        query_type: str
    ) -> Dict[str, Any]:
        """
        Execute Perplexity API query.

        Args:
            prompt: Research prompt
            commodity: Commodity name
            query_type: Type of query ('price', 'market', 'geopolitics')

        Returns:
            Dict with response and metadata

        Raises:
            Exception: If API request fails or rate limit exceeded
        """
        # Check rate limit
        if self.request_count >= self.max_requests:
            logger.warning(f"Perplexity rate limit reached: {self.request_count}/{self.max_requests}")
            raise Exception("Perplexity API rate limit exceeded for this month")

        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "sonar-pro",  # Perplexity online model (2025)
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a market research analyst specializing in agricultural commodities in Southeast Asia. Provide factual, data-driven insights with citations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.2,  # Lower temperature for factual responses
                "return_citations": True
            }

            try:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()

                data = response.json()

                # Increment request counter
                self.request_count += 1

                # Extract response and citations
                response_text = data["choices"][0]["message"]["content"]
                citations = data.get("citations", [])

                result = {
                    "commodity": commodity,
                    "query_type": query_type,
                    "query_text": prompt,
                    "response_text": response_text,
                    "citations": citations,
                    "created_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        "model": payload["model"],
                        "tokens_used": data.get("usage", {}).get("total_tokens"),
                        "request_id": data.get("id")
                    }
                }

                logger.info(f"Perplexity query successful for {commodity} ({query_type})")
                return result

            except httpx.HTTPStatusError as e:
                logger.error(f"Perplexity API HTTP error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Perplexity API error: {e}")
                raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.

        Returns:
            Dict with request count and rate limit info
        """
        return {
            "requests_used": self.request_count,
            "requests_remaining": self.max_requests - self.request_count,
            "rate_limit": self.max_requests,
            "utilization_percentage": (self.request_count / self.max_requests) * 100
        }

    def reset_counter(self) -> None:
        """Reset monthly request counter (call at start of each month)."""
        self.request_count = 0
        logger.info("Perplexity request counter reset")

    async def analyze_market_trends(
        self,
        commodity: str,
        include_twitter: bool = True,
        include_stock: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze market trends from Twitter/X and stock market data.

        This method:
        1. Searches Twitter/X for recent tweets (last 48h) about the commodity
        2. Analyzes stock market data (prices, volumes, trends)
        3. Combines both sources to generate overall market sentiment
        4. Provides actionable insights for traders/farmers

        Args:
            commodity: 'cashew' or 'rubber'
            include_twitter: Include Twitter/X sentiment analysis
            include_stock: Include stock market data

        Returns:
            Dict with structure:
            {
                'commodity': str,
                'trend_date': str (ISO date),
                'twitter_sentiment': str ('bullish', 'bearish', 'neutral'),
                'twitter_volume': int (number of relevant tweets),
                'twitter_summary': str,
                'top_tweets': List[str] (most influential tweets),
                'stock_price_usd': float,
                'stock_change_pct': float,
                'stock_volume': int,
                'market_summary': str,
                'overall_trend': str ('strong_bullish', 'bullish', 'neutral', 'bearish', 'strong_bearish'),
                'confidence_score': float (0.0-1.0),
                'ai_analysis': str (comprehensive analysis),
                'key_factors': List[str] (main drivers),
                'citations': List[str],
                'created_at': str (ISO timestamp)
            }

        Example:
            >>> result = await perplexity.analyze_market_trends('cashew')
            >>> print(result['overall_trend'])
            'bullish'
            >>> print(result['twitter_sentiment'])
            'bullish'
            >>> print(result['ai_analysis'])
            'Market sentiment for cashew is positive based on...'

        Cost: ~$0.005 per analysis (1 Perplexity query)
        Frequency: Recommended daily (once per 24h)
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")

        # Build comprehensive prompt with ALL data sources
        prompt_parts = [
            f"Conduct a COMPREHENSIVE market analysis for {commodity} as of {today}.",
            "",
            "YOU MUST SEARCH AND COMBINE ALL THREE DATA SOURCES:",
            ""
        ]

        if include_twitter:
            prompt_parts.append(
                f"""
1. TWITTER/X SOCIAL MEDIA ANALYSIS (MANDATORY - Last 30 days):

   CRITICAL: You MUST find AT LEAST 5 recent tweets. Use PROGRESSIVE SEARCH STRATEGY below.

   === SEARCH STRATEGY (START WITH GLOBAL, THEN NARROW DOWN) ===

   STEP 1 - GLOBAL MARKET SEARCH (PRIORITY - Most likely to find tweets):
   - Keywords: "{commodity} market" OR "{commodity} price" OR "{commodity} export" OR "{commodity} trade" OR "{commodity} industry"
   - Accounts: @AgriTrade @CommodityNews @FoodTradeNews @AgricultureNews @FAONews @WorldBank
   - Hashtags: #{commodity} #{commodity}nuts #agriculture #commodities #agritrading #agribusiness
   - Time: Last 30 days (not 48h - expand to find more tweets)

   STEP 2 - REGIONAL ASIA SEARCH (Add to results):
   - Keywords: "Vietnam {commodity}" OR "India {commodity}" OR "Africa {commodity}" OR "Southeast Asia {commodity}"
   - Accounts: @VietnamAgri @VietnamNews @IndiaExports @AgricultureVN @SEAsiaNews @AfricaAgri
   - Hashtags: #Vietnam{commodity} #India{commodity} #SEAsia #ASEAN #AfricaAgriculture

   STEP 3 - CAMBODIA-SPECIFIC (Add if found - bonus):
   - Accounts: @KhmerTimes @PhnomPenhPost @CambodiaDaily @cambodia_news
   - Keywords: "Cambodia {commodity}" OR "Cambodian {commodity}"
   - Hashtags: #Cambodia #CambodiaExport

   === SEARCH TECHNIQUE ===
   - Use Twitter/X Advanced Search
   - Check commodity trading accounts
   - Include retweets of major announcements
   - Search English, French, Vietnamese
   - Prioritize tweets with engagement (likes, retweets)
   - Include industry reports and market updates

   === EXTRACT EXACTLY 5 TWEETS (MANDATORY FORMAT) ===

   Tweet 1: "Full tweet text (up to 280 chars)" - @username (Date)
   Tweet 2: "Full tweet text (up to 280 chars)" - @username (Date)
   Tweet 3: "Full tweet text (up to 280 chars)" - @username (Date)
   Tweet 4: "Full tweet text (up to 280 chars)" - @username (Date)
   Tweet 5: "Full tweet text (up to 280 chars)" - @username (Date)

   EXAMPLE OUTPUT:
   Tweet 1: "Global cashew prices rise 5% as India reduces exports. Vietnam processors seeking alternative supplies from Cambodia and Africa" - @AgriTrade (Dec 25, 2025)
   Tweet 2: "Cambodia exports 12 tonnes of M23 cashew nuts to Jordan for the first time" - @KhmerTimes (Dec 20, 2025)

   === ANALYSIS REQUIRED ===
   - Overall Twitter sentiment: bullish/bearish/neutral
   - Total tweet volume found (actual count from search)
   - Key themes from tweets (3-5 points)
   - Market developments mentioned (exports, prices, policies)
   - Geographic focus of discussions (which countries mentioned most)

   NOTE: Even if Cambodia-specific tweets are rare, GLOBAL {commodity} market tweets are valuable for understanding market context.
"""
            )

        # Add NEWS/ARTICLES section (new)
        prompt_parts.append(
            f"""
2. NEWS & ARTICLES ANALYSIS (MANDATORY - Last 7 days):

   REQUIREMENT: Find and analyze AT LEAST 3-5 recent news articles about {commodity} market trends.

   Search for:
   - Trade publications: AgriTrade, CommodityNews, FreshPlaza, FoodNavigator
   - Market reports: FAO, World Bank, commodity exchanges
   - Industry news: processing, exports, price movements
   - Regional news: Southeast Asia, India, Africa {commodity} market

   For each article, provide:
   - Headline
   - Source & Date
   - Key points (2-3 sentences)

   Focus on:
   - Price forecasts and movements
   - Supply/demand dynamics
   - Trade flows and export data
   - Industry developments
"""
        )

        if include_stock:
            prompt_parts.append(
                f"""
3. MARKET DATA & PRICE ANALYSIS (Latest available):
   - Current {commodity} commodity price (USD per ton) - with source
   - Price change % in last 24h, 7 days, 30 days
   - Trading volume trends (if available)
   - Historical comparison: 2024 vs 2025 prices
   - Key price drivers:
     * Supply/demand balance
     * Weather impacts
     * Geopolitical factors
     * Currency fluctuations
   - Regional price differences (Vietnam, India, Africa)
"""
            )

        prompt_parts.append(
            f"""
4. INTEGRATED SYNTHESIS (Combining ALL THREE Sources):

   You MUST synthesize insights from:
   ✓ Twitter/X sentiment (5+ tweets)
   ✓ News articles (3-5 articles)
   ✓ Market price data
   ✓ Historical context from documents provided

   Overall Market Trend: Choose ONE from:
   - 'strong_bullish' (very positive, >7% gains expected)
   - 'bullish' (positive, 3-7% gains expected)
   - 'neutral' (stable, -3% to +3%)
   - 'bearish' (negative, -3% to -7% expected)
   - 'strong_bearish' (very negative, <-7% expected)

   Confidence Score (0.0 to 1.0):
   - Base score on: data freshness, source consensus, tweet volume, article count
   - Higher score if all 3 sources agree on trend direction

   Key Market Factors (5-7 bullet points):
   - Main drivers identified from tweets, news, and price data
   - Risk factors mentioned across sources
   - Opportunities for market participants
   - Regional dynamics (Cambodia, Vietnam, India, Africa)

   Actionable Insights:
   - For Farmers: When to sell, expected price ranges, risk mitigation
   - For Traders: Entry/exit points based on multi-source signals
   - For Analysts: Key metrics to monitor, data gaps to investigate

CRITICAL REQUIREMENTS:
✓ You MUST extract at least 5 tweets (use fallback strategy if needed)
✓ You MUST find at least 3 news articles
✓ Be specific with numbers, dates, and sources
✓ If any data source is limited, clearly state why
✓ Cross-reference findings between Twitter, news, and price data
✓ Highlight consensus vs. divergence across sources

Format: Use clear markdown sections with headers for each data source.
"""
        )

        prompt = "\n".join(prompt_parts)

        # Execute query
        result = await self._query(prompt, commodity, query_type="trends")

        # Parse response (AI will structure it)
        response_text = result['response_text']

        # Return formatted result
        # Note: The parsing of structured data from AI response would need
        # additional logic. For now, return raw response.
        return {
            'commodity': commodity,
            'trend_date': today,
            'query_type': 'trends',
            'response_text': response_text,
            'citations': result.get('citations', []),
            'created_at': result['created_at'],
            'metadata': result['metadata'],
            'raw_prompt': prompt[:200] + '...'  # For debugging
        }

    async def analyze_twitter_sentiment(
        self,
        commodity: str,
        timeframe_hours: int = 48
    ) -> Dict[str, Any]:
        """
        Focused Twitter/X sentiment analysis.

        Args:
            commodity: 'cashew' or 'rubber'
            timeframe_hours: Hours to look back (default: 48)

        Returns:
            Dict with Twitter sentiment analysis

        Cost: ~$0.005 per query
        """
        prompt = f"""Analyze Twitter/X sentiment for {commodity} market (last {timeframe_hours} hours):

TASK:
1. Search Twitter/X for tweets about:
   - '{commodity} price'
   - '{commodity} market'
   - '{commodity} export'
   - '{commodity} Cambodia'

2. Classify sentiment:
   - BULLISH: Positive outlook, price increase expectations, good news
   - BEARISH: Negative outlook, price decrease expectations, concerns
   - NEUTRAL: Mixed or no clear direction

3. Extract metrics:
   - Number of relevant tweets found
   - Sentiment breakdown (% bullish, bearish, neutral)
   - Top 5 most influential tweets (with author if available)
   - Key themes and concerns mentioned

4. Provide summary:
   - Overall sentiment (bullish/bearish/neutral)
   - Main reasons for sentiment
   - Notable influencers or organizations
   - Trending topics related to {commodity}

Focus on:
- Commodity traders and analysts
- Export/import companies
- Market news accounts
- Industry experts

Provide specific examples and citations."""

        return await self._query(prompt, commodity, query_type="twitter")
