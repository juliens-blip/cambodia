"""Market trends monitoring service using Perplexity AI for Twitter/X and stock analysis."""
import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, date

from app.services.supabase_service import SupabaseService
from app.services.cambodia_macro_service import CambodiaMacroService
from app.services.perplexity_service import PerplexityService

logger = logging.getLogger(__name__)


class MarketTrendsService:
    """Service for analyzing and storing market trends from Twitter/X and stock data."""

    def __init__(
        self,
        supabase: SupabaseService,
        perplexity: PerplexityService,
        macro_service: Optional[CambodiaMacroService] = None
    ):
        """
        Initialize market trends service.

        Args:
            supabase: SupabaseService instance
            perplexity: PerplexityService instance
        """
        self.supabase = supabase
        self.perplexity = perplexity
        self.macro_service = macro_service
        if self.macro_service is None:
            try:
                self.macro_service = CambodiaMacroService(supabase)
            except Exception as exc:
                logger.warning("CambodiaMacroService unavailable: %s", exc)
                self.macro_service = None

        logger.info("MarketTrendsService initialized")

    async def analyze_and_store_trends(
        self,
        commodity: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze market trends and store in database.

        Args:
            commodity: 'cashew' or 'rubber'
            force_refresh: Force new analysis even if today's exists

        Returns:
            Dict with analysis results and storage status
        """
        today = date.today()

        # Check if analysis already exists for today
        if not force_refresh:
            existing = await self._get_today_trend(commodity)
            if existing:
                logger.info(f"Trend already exists for {commodity} on {today}")
                return {
                    'status': 'exists',
                    'data': existing,
                    'message': f'Trend for {commodity} already analyzed today'
                }

        logger.info(f"Analyzing market trends for {commodity}...")

        # Step 1: Build macro context if available
        macro_context = ""
        if self.macro_service:
            try:
                macro_context = await self.macro_service.build_macro_context_text(commodity)
            except Exception as e:
                logger.warning("Macro context fetch failed: %s", e)
                macro_context = ""

        # Step 2: Get Perplexity analysis
        try:
            analysis = await self.perplexity.analyze_market_trends(
                commodity=commodity,
                include_twitter=True,
                include_stock=True,
                macro_context=macro_context
            )

        except Exception as e:
            logger.error(f"Error getting Perplexity analysis: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to get market analysis'
            }

        # Step 3: Parse AI response
        parsed = self._parse_analysis(analysis['response_text'], commodity)

        # Step 4: Build database record
        trend_data = {
            'commodity': commodity,
            'trend_date': today.isoformat(),

            # Twitter data
            'twitter_sentiment': parsed.get('twitter_sentiment', 'neutral'),
            'twitter_volume': parsed.get('twitter_volume', 0),
            'twitter_summary': parsed.get('twitter_summary', ''),
            'top_tweets': parsed.get('top_tweets', []),
            'tweet_count': len(parsed.get('top_tweets', [])),

            # News articles data (new)
            'news_articles': parsed.get('news_articles', []),
            'news_summary': parsed.get('news_summary', ''),

            # Stock data
            'stock_price_usd': parsed.get('stock_price'),
            'stock_change_pct': parsed.get('stock_change_pct'),
            'stock_volume': parsed.get('stock_volume'),
            'market_summary': parsed.get('market_summary', ''),

            # Combined analysis
            'overall_trend': parsed.get('overall_trend', 'neutral'),
            'confidence_score': parsed.get('confidence_score', 0.5),
            'ai_analysis': analysis['response_text'],  # Full text
            'key_factors': parsed.get('key_factors', []),

            # Metadata
            'data_sources': parsed.get('sources', []),
            'perplexity_citations': analysis.get('citations', [])
        }

        # Step 5: Store in database (update if today's record exists)
        try:
            table = self.supabase.client.table("market_trends")
            existing = table.select("id").eq("commodity", commodity).eq(
                "trend_date", trend_data["trend_date"]
            ).execute().data

            if existing:
                record_id = existing[0]["id"]
                result = table.update(trend_data).eq("id", record_id).execute()
                action = "updated"
            else:
                result = table.insert(trend_data).execute()
                action = "inserted"

            logger.info(f"Trend {action} successfully for {commodity} on {today}")

            return {
                'status': 'success',
                'data': result.data[0] if result.data else trend_data,
                'message': f'Trend analysis {action} for {commodity}'
            }

        except Exception as e:
            logger.error(f"Error storing trend: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Analysis completed but storage failed',
                'data': trend_data  # Return data anyway
            }

    def _parse_analysis(self, response_text: str, commodity: str = 'cashew') -> Dict[str, Any]:
        """
        Parse Perplexity AI response to extract structured data.

        Args:
            response_text: Raw AI response
            commodity: Commodity name for validation

        Returns:
            Dict with extracted fields
        """
        parsed = {}

        # Extract Twitter sentiment
        if 'bullish' in response_text.lower():
            if 'strong' in response_text.lower() and 'bullish' in response_text.lower():
                parsed['twitter_sentiment'] = 'bullish'
                parsed['overall_trend'] = 'strong_bullish'
            else:
                parsed['twitter_sentiment'] = 'bullish'
                parsed['overall_trend'] = 'bullish'
        elif 'bearish' in response_text.lower():
            if 'strong' in response_text.lower() and 'bearish' in response_text.lower():
                parsed['twitter_sentiment'] = 'bearish'
                parsed['overall_trend'] = 'strong_bearish'
            else:
                parsed['twitter_sentiment'] = 'bearish'
                parsed['overall_trend'] = 'bearish'
        else:
            parsed['twitter_sentiment'] = 'neutral'
            parsed['overall_trend'] = 'neutral'

        # Extract tweet volume (look for numbers + "tweets")
        tweet_match = re.search(r'(\d+)\s+tweets?', response_text, re.IGNORECASE)
        if tweet_match:
            parsed['twitter_volume'] = int(tweet_match.group(1))
        else:
            parsed['twitter_volume'] = 0

        # Extract stock price change percentage
        pct_matches = re.findall(r'([+-]?\d+\.?\d*)\s*%', response_text)
        if pct_matches:
            # Take the most prominent percentage
            parsed['stock_change_pct'] = float(pct_matches[0].replace('+', ''))

        # Extract price (look for USD per ton)
        price_match = re.search(r'\$?(\d+(?:,\d{3})*)\s*(?:USD)?\s*per\s*ton', response_text, re.IGNORECASE)
        if price_match:
            price_str = price_match.group(1).replace(',', '')
            parsed['stock_price_usd'] = float(price_str)

        # Extract confidence score
        conf_match = re.search(r'confidence.*?(\d+\.?\d*)\s*/\s*1\.0', response_text, re.IGNORECASE)
        if conf_match:
            parsed['confidence_score'] = float(conf_match.group(1))
        else:
            # Default confidence based on data quality
            parsed['confidence_score'] = 0.7 if parsed.get('twitter_volume', 0) > 10 else 0.5

        # Extract key factors (look for bullet points)
        factors = []
        lines = response_text.split('\n')
        for line in lines:
            if line.strip().startswith(('•', '-', '*', '·')):
                factor = line.strip().lstrip('•-*· ')
                if len(factor) > 10:  # Meaningful factor
                    factors.append(factor)

        parsed['key_factors'] = factors[:5]  # Top 5

        # Extract top tweets (improved parsing for multiple Perplexity response formats)
        tweets = []

        # Pattern 1: "Tweet X: "text" - @username (Date)" format (standard)
        tweet_pattern_new = r'Tweet\s+\d+:\s*["\\"]+([^"\\]{20,350})["\\"]+\s*-\s*@(\w+)\s*\(([^)]+)\)'
        for match in re.finditer(tweet_pattern_new, response_text):
            tweet_text = match.group(1)
            username = match.group(2)
            date = match.group(3)
            tweets.append({
                'text': tweet_text,
                'username': username,
                'created_at': date,
                'likes': 0,
                'retweets': 0
            })

        # Pattern 2: "- Tweet X: "text" - @username (Date)" with leading dash
        if len(tweets) == 0:
            tweet_pattern_dash = r'-\s*Tweet\s+\d+:\s*["\\"]+([^"\\]{20,350})["\\"]+\s*-\s*@(\w+)\s*\(([^)]+)\)'
            for match in re.finditer(tweet_pattern_dash, response_text):
                tweets.append({
                    'text': match.group(1),
                    'username': match.group(2),
                    'created_at': match.group(3),
                    'likes': 0,
                    'retweets': 0
                })

        # Pattern 3: Escaped quotes format (from JSON): \"text\" - @username
        if len(tweets) == 0:
            tweet_pattern_escaped = r'\\"([^\\]{20,350})\\"[^@]*@(\w+)[^(]*\(([^)]+)\)'
            for match in re.finditer(tweet_pattern_escaped, response_text):
                tweets.append({
                    'text': match.group(1),
                    'username': match.group(2),
                    'created_at': match.group(3),
                    'likes': 0,
                    'retweets': 0
                })

        # Pattern 4: Simple format with @username after quote
        if len(tweets) == 0:
            tweet_pattern_simple = r'"([^"]{20,350})"\s*[-–—]\s*@(\w+)'
            for match in re.finditer(tweet_pattern_simple, response_text):
                tweets.append({
                    'text': match.group(1),
                    'username': match.group(2),
                    'created_at': 'Recent',
                    'likes': 0,
                    'retweets': 0
                })

        # Pattern 5: Last resort - extract any substantial quoted text
        if len(tweets) == 0:
            tweet_pattern_fallback = r'"([^"]{30,280})"'
            tweet_matches = re.findall(tweet_pattern_fallback, response_text)
            for tweet_text in tweet_matches[:5]:
                # Skip analysis text, only keep tweet-like content
                if any(word in tweet_text.lower() for word in ['cashew', 'rubber', 'price', 'export', 'market', 'trade']):
                    tweets.append({
                        'text': tweet_text,
                        'username': 'market_source',
                        'created_at': 'Recent',
                        'likes': 0,
                        'retweets': 0
                    })

        parsed['top_tweets'] = tweets[:5]  # Max 5 tweets
        logger.info(f"Parsed {len(parsed['top_tweets'])} tweets from response")

        # Extract news articles (new)
        articles = []

        # Pattern for news articles with headline, source, and date
        article_pattern = r'(?:Article|Headline).*?:\s*"([^"]{20,200})"\s*-\s*([^(]+)\s*\(([^)]+)\)'
        for match in re.finditer(article_pattern, response_text):
            headline = match.group(1)
            source = match.group(2).strip()
            date = match.group(3)
            articles.append({
                'headline': headline,
                'source': source,
                'date': date,
                'url': None  # Perplexity doesn't provide direct URLs
            })

        # Fallback: Extract from bullet points mentioning sources
        if len(articles) == 0:
            # Look for lines like "- Source Name (Date): headline text"
            article_pattern_alt = r'-\s*([A-Za-z\s]+)\s*\(([^)]+)\):\s*([^.]+)'
            for match in re.finditer(article_pattern_alt, response_text):
                if len(match.group(3)) > 30:  # Meaningful headline
                    articles.append({
                        'headline': match.group(3).strip(),
                        'source': match.group(1).strip(),
                        'date': match.group(2),
                        'url': None
                    })

        parsed['news_articles'] = articles[:5]  # Max 5 articles

        # Create summaries
        parsed['twitter_summary'] = self._extract_section(response_text, 'TWITTER', 'NEWS')
        parsed['news_summary'] = self._extract_section(response_text, 'NEWS', 'MARKET DATA')
        parsed['market_summary'] = self._extract_section(response_text, 'MARKET DATA', 'INTEGRATED')

        # Validate prices for Cambodia cashew (Phase 1.2)
        parsed = self._validate_prices_cambodia(parsed, 'cashew')

        # Validate prices for Cambodia rubber
        if commodity == 'rubber':
            parsed = self._validate_rubber_prices(parsed)

        return parsed

    def _validate_rubber_prices(self, parsed: Dict) -> Dict:
        """
        Validate rubber price ranges for Cambodia market.

        Expected ranges (2024-2025):
        - Global spot: 170-190 cents/kg (1,700-1,900 USD/ton)
        - FOB Cambodia: 1,750-1,900 USD/ton
        - Farmgate Cambodia: 4,500-6,000 KHR/kg

        Args:
            parsed: Parsed data dict from _parse_analysis

        Returns:
            Enhanced dict with price validation and context
        """
        warnings = []
        price_usd_ton = parsed.get('stock_price_usd') or parsed.get('stock_price')

        if price_usd_ton:
            # Validate global spot price range
            if price_usd_ton < 1400:
                warnings.append(
                    f"⚠️ Rubber price ${price_usd_ton:,.0f}/t very low "
                    f"(expected 1,700-1,900 USD/ton)"
                )
                parsed['price_context'] = 'Below typical range - market downturn or data issue'
            elif 1400 <= price_usd_ton < 1700:
                warnings.append(
                    f"⚠️ Rubber price ${price_usd_ton:,.0f}/t below typical range "
                    f"(expected 1,700-1,900 USD/ton)"
                )
                parsed['price_context'] = 'Low end - bearish market conditions'
            elif 1700 <= price_usd_ton <= 1900:
                parsed['price_context'] = 'Normal range - stable market'
            elif 1901 <= price_usd_ton <= 2500:
                warnings.append(
                    f"⚠️ Rubber price ${price_usd_ton:,.0f}/t above typical range "
                    f"(expected 1,700-1,900 USD/ton)"
                )
                parsed['price_context'] = 'High end - bullish market conditions'
            else:  # > 2500
                warnings.append(
                    f"⚠️ Rubber price ${price_usd_ton:,.0f}/t very high "
                    f"(expected 1,700-1,900 USD/ton) - verify source"
                )
                parsed['price_context'] = 'Above typical range - exceptional market surge'

            # Calculate farmgate estimate (assuming ~70% of FOB for farmers)
            farmgate_usd_kg = (price_usd_ton / 1000) * 0.70
            farmgate_khr_kg = farmgate_usd_kg * 4050  # USD/KHR rate

            parsed['farmgate_estimate_usd_kg'] = round(farmgate_usd_kg, 2)
            parsed['farmgate_estimate_khr_kg'] = round(farmgate_khr_kg, 0)

            # Validate farmgate range
            if farmgate_khr_kg < 3000:
                warnings.append(
                    f"⚠️ Estimated farmgate {farmgate_khr_kg:,.0f} KHR/kg very low "
                    f"(expected 4,500-6,000 KHR/kg) - farmer crisis risk"
                )
            elif farmgate_khr_kg > 7000:
                warnings.append(
                    f"✓ Estimated farmgate {farmgate_khr_kg:,.0f} KHR/kg high "
                    f"(expected 4,500-6,000 KHR/kg) - favorable for farmers"
                )

        # Add clarification footer for UI display
        parsed['price_clarification'] = """RUBBER PRICE REFERENCE (Cambodia)

Product Type:
- Natural rubber (latex/sheet form)
- Minimal processing in Cambodia (exported raw)

Typical Ranges (2024-2025):
- Global spot (TSR20): 170-190 cents/kg (1,700-1,900 USD/ton)
- FOB Cambodia: ~1,750-1,900 USD/ton
- Farmgate Cambodia: 4,500-6,000 KHR/kg (estimated)

Market Structure:
- Cambodia production: ~120,000 tons/year
- 95% exports raw (China 60%, Vietnam 20%)
- Price-taker (follows global TSR20/RSS3 benchmarks)
- No domestic processing capacity

FX Impact:
- USD/KHR rate affects farmer revenues
- KHR weakens → Farmers gain (more KHR per USD export)
- KHR strengthens → Farmers lose (less KHR per USD export)

Cambodia Context:
- ~80,000 farming families
- Main provinces: Kampong Cham (35%), Kratié (25%), Mondulkiri (20%)
- Dependency: HIGH (rubber = primary cash crop)
- Vulnerability: 60% exports to China (demand risk)"""

        parsed['price_warnings'] = warnings
        parsed['price_type'] = 'Natural Rubber (TSR20/RSS3)'

        # Log for debugging
        if price_usd_ton:
            logger.info(
                f"Rubber price validation: ${price_usd_ton:,.0f}/t → "
                f"Farmgate est: {parsed.get('farmgate_estimate_khr_kg', 0):,.0f} KHR/kg "
                f"({parsed.get('price_context', 'unknown')})"
            )

        return parsed

    def _validate_prices_cambodia(self, parsed: Dict, commodity: str) -> Dict:
        """
        Validate price ranges for Cambodia cashew market.

        Adds price_type, price_context, and price_clarification fields.
        Detects if price is RCN ($1,500-2,500) or Kernels ($6,000-7,000).

        Args:
            parsed: Parsed data dict from _parse_analysis
            commodity: Commodity name (validation only applies to 'cashew')

        Returns:
            Enhanced dict with price context and clarification
        """
        if commodity != 'cashew':
            return parsed

        warnings = []
        price = parsed.get('stock_price_usd') or parsed.get('stock_price')

        if price:
            # Detect if RCN or Kernels based on price range
            if 1000 <= price <= 3000:
                parsed['price_type'] = 'RCN'
                parsed['price_context'] = 'Raw Cashew Nuts (FOB Cambodia)'
                parsed['price_segment'] = 'raw'
            elif 3001 <= price <= 5000:
                parsed['price_type'] = 'RCN'
                parsed['price_context'] = 'Raw Cashew Nuts (High quality or premium market)'
                parsed['price_segment'] = 'raw_premium'
                warnings.append(f"Price ${price:,.0f}/t is in upper RCN range - may indicate premium quality or market surge")
            elif 5001 <= price <= 9000:
                parsed['price_type'] = 'Kernels'
                parsed['price_context'] = 'Processed Kernels (FOB Vietnam)'
                parsed['price_segment'] = 'kernels'
            elif price > 9000:
                parsed['price_type'] = 'Kernels'
                parsed['price_context'] = 'Premium Kernels W180/W240 (FOB Vietnam)'
                parsed['price_segment'] = 'kernels_premium'
                warnings.append(f"High price ${price:,.0f}/t - likely premium kernels W180/W240")
            else:
                parsed['price_type'] = 'Unknown'
                parsed['price_context'] = 'Price outside expected ranges'
                parsed['price_segment'] = 'unknown'
                warnings.append(f"Price ${price:,.0f}/t outside expected ranges")

        # Add clarification footer for UI display
        parsed['price_clarification'] = """PRICE REFERENCE GUIDE (Cambodia Cashew)

Product Types:
- RCN (Raw Cashew Nuts): Unprocessed, exported to Vietnam - $1,500-2,500/ton
- Kernels: Processed cashew nuts - $6,000-7,000/ton (W320 grade)

Quality Grades (Kernels):
- W180 (Premium): Largest kernels, highest price ($7,000-9,000+)
- W240 (High): Large kernels ($6,500-7,500)
- W320 (Standard): Most traded grade ($6,000-7,000)
- W450 (Economy): Smaller kernels, lower price ($5,500-6,500)

Cambodia Context:
- 2nd largest RCN producer globally
- 90% exports to Vietnam for processing
- ~500,000 farming families"""

        parsed['price_warnings'] = warnings

        # Log for debugging
        if price:
            logger.info(
                f"Cambodia price validation: ${price:,.0f}/t -> {parsed.get('price_type')} "
                f"({parsed.get('price_context')})"
            )

        return parsed

    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> str:
        """Extract text between two markers."""
        start_idx = text.upper().find(start_marker)
        end_idx = text.upper().find(end_marker)

        if start_idx != -1:
            if end_idx != -1:
                section = text[start_idx:end_idx]
            else:
                section = text[start_idx:start_idx+500]  # First 500 chars

            # Clean up
            lines = [l.strip() for l in section.split('\n') if l.strip()]
            return ' '.join(lines[:3])  # First 3 meaningful lines

        return ""

    async def _get_today_trend(self, commodity: str) -> Optional[Dict[str, Any]]:
        """Get today's trend if it exists."""
        today = date.today().isoformat()

        try:
            result = self.supabase.client.table("market_trends").select("*").eq(
                "commodity", commodity
            ).eq("trend_date", today).execute()

            if result.data:
                return result.data[0]

        except Exception as e:
            logger.error(f"Error checking existing trend: {e}")

        return None

    async def get_latest_trend(self, commodity: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent trend analysis for a commodity.

        Args:
            commodity: 'cashew' or 'rubber'

        Returns:
            Latest trend dict or None (includes all fields: top_tweets, tweet_count, etc.)
        """
        try:
            # Direct query to get ALL fields including top_tweets and tweet_count
            result = self.supabase.client.table("market_trends").select("*").eq(
                "commodity", commodity
            ).order("trend_date", desc=True).limit(1).execute()

            if result.data:
                trend = result.data[0]
                # Ensure tweet_count is set from top_tweets if missing
                if 'tweet_count' not in trend or trend.get('tweet_count') is None:
                    tweets = trend.get('top_tweets', [])
                    trend['tweet_count'] = len(tweets) if tweets else 0
                logger.info(f"get_latest_trend for {commodity}: tweet_count={trend.get('tweet_count')}, top_tweets count={len(trend.get('top_tweets', []))}")
                return trend

        except Exception as e:
            logger.error(f"Error getting latest trend: {e}")

        return None

    async def get_trend_history(
        self,
        commodity: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get trend history for a commodity.

        Args:
            commodity: 'cashew' or 'rubber'
            days: Number of days to look back

        Returns:
            List of trend records
        """
        try:
            result = self.supabase.client.table("market_trends").select("*").eq(
                "commodity", commodity
            ).order("trend_date", desc=True).limit(days).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting trend history: {e}")
            return []

    async def get_unread_alerts(self) -> List[Dict[str, Any]]:
        """Get unread trend alerts."""
        try:
            result = self.supabase.client.rpc("get_unread_alerts").execute()
            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []

    async def mark_alert_read(self, alert_id: str) -> bool:
        """Mark an alert as read."""
        try:
            self.supabase.client.table("trend_alerts").update({
                "is_read": True
            }).eq("id", alert_id).execute()

            return True

        except Exception as e:
            logger.error(f"Error marking alert as read: {e}")
            return False
