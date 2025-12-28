# Prompt Perplexity Complet - 3 Sources de Données

**Date:** 2025-12-27 22:45
**Status:** ✅ IMPLÉMENTÉ

---

## 🎯 Objectif

Forcer Perplexity à chercher et combiner **TOUTES les sources** simultanément:

1. ✅ **5+ tweets minimum** (Twitter/X social media)
2. ✅ **3-5 articles récents** (News & publications)
3. ✅ **Données de marché** (Prix, volumes, trends)
4. ✅ **Historique documentaire** (PDFs fournis via RAG context)

---

## 📝 Nouveau Prompt

### Section 1: TWITTER/X ANALYSIS (MANDATORY)

```
REQUIREMENT: You MUST find and extract AT LEAST 5 recent tweets about cashew market.

Search Strategy:
- Hashtags: #cashew #cashewnuts #agriculture #commodities #trading
- Keywords: "cashew market" OR "cashew price" OR "cashew export" OR "cashew trade"
- Regions: Southeast Asia, India, Africa, global commodity traders
- Accounts: @AgriTrade @CommodityNews @FoodTradeNews agriculture traders
- Time: Last 7 days minimum

EXTRACT EXACTLY 5 TWEETS:

Tweet 1: "Full tweet text (up to 280 chars)" - @username (Dec 25, 2025)
Tweet 2: "Full tweet text (up to 280 chars)" - @username (Dec 24, 2025)
Tweet 3: "Full tweet text (up to 280 chars)" - @username (Dec 23, 2025)
Tweet 4: "Full tweet text (up to 280 chars)" - @username (Dec 22, 2025)
Tweet 5: "Full tweet text (up to 280 chars)" - @username (Dec 21, 2025)

IF you cannot find 5 tweets about cashew specifically:
- Search "agriculture commodities" or "food trade"
- Search tweets mentioning Vietnam, Cambodia, India exports
- Search general agricultural commodity market sentiment

Then provide:
- Overall Twitter sentiment: bullish/bearish/neutral
- Total tweet volume found
- Key themes from tweets (3-5 points)
- Market concerns mentioned
```

**Améliorations:**
- ✅ Hashtags spécifiques suggérés
- ✅ Comptes Twitter suggérés
- ✅ Stratégie de fallback si 0 tweets spécifiques
- ✅ Format structuré obligatoire

---

### Section 2: NEWS & ARTICLES ANALYSIS (NEW - MANDATORY)

```
REQUIREMENT: Find and analyze AT LEAST 3-5 recent news articles about cashew market trends.

Search for:
- Trade publications: AgriTrade, CommodityNews, FreshPlaza, FoodNavigator
- Market reports: FAO, World Bank, commodity exchanges
- Industry news: processing, exports, price movements
- Regional news: Southeast Asia, India, Africa cashew market

For each article, provide:
- Headline
- Source & Date
- Key points (2-3 sentences)

Focus on:
- Price forecasts and movements
- Supply/demand dynamics
- Trade flows and export data
- Industry developments
```

**Nouveautés:**
- ✅ **Section NEWS explicite** (n'existait pas avant)
- ✅ Sources suggérées (AgriTrade, FAO, etc.)
- ✅ Format structuré pour articles
- ✅ Minimum 3-5 articles requis

---

### Section 3: MARKET DATA & PRICE ANALYSIS

```
- Current cashew commodity price (USD per ton) - with source
- Price change % in last 24h, 7 days, 30 days
- Trading volume trends (if available)
- Historical comparison: 2024 vs 2025 prices
- Key price drivers:
  * Supply/demand balance
  * Weather impacts
  * Geopolitical factors
  * Currency fluctuations
- Regional price differences (Vietnam, India, Africa)
```

**Améliorations:**
- ✅ Demande de comparaison historique explicite
- ✅ Prix régionaux (Vietnam, India, Africa)
- ✅ Sources obligatoires

---

### Section 4: INTEGRATED SYNTHESIS

```
You MUST synthesize insights from:
✓ Twitter/X sentiment (5+ tweets)
✓ News articles (3-5 articles)
✓ Market price data
✓ Historical context from documents provided

CRITICAL REQUIREMENTS:
✓ You MUST extract at least 5 tweets (use fallback strategy if needed)
✓ You MUST find at least 3 news articles
✓ Be specific with numbers, dates, and sources
✓ Cross-reference findings between Twitter, news, and price data
✓ Highlight consensus vs. divergence across sources
```

**Améliorations:**
- ✅ Checklist explicite des 4 sources
- ✅ Requiert cross-référencement
- ✅ Consensus/divergence entre sources

---

## 🔧 Parsing Amélioré

### Extraction Tweets

**Code:** `app/services/market_trends_service.py` lignes 203-235

```python
# Pattern 1: "Tweet X: "text" - @username (Date)" format
tweet_pattern_new = r'Tweet\s+\d+:\s*"([^"]{20,280})"\s*-\s*@(\w+)\s*\(([^)]+)\)'
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

# Pattern 2: Fallback (old format)
if len(tweets) == 0:
    tweet_pattern_old = r'"([^"]{20,280})"'
    # ...
```

**Résultat:**
```json
{
  "top_tweets": [
    {
      "text": "Vietnam cashew exports surge...",
      "username": "AgriTradeNews",
      "created_at": "Dec 26, 2025",
      "likes": 0,
      "retweets": 0
    }
  ]
}
```

---

### Extraction News Articles (NEW)

**Code:** `app/services/market_trends_service.py` lignes 237-266

```python
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
        'url': None
    })

# Fallback: Extract from bullet points
if len(articles) == 0:
    article_pattern_alt = r'-\s*([A-Za-z\s]+)\s*\(([^)]+)\):\s*([^.]+)'
    # ...

parsed['news_articles'] = articles[:5]  # Max 5 articles
```

**Résultat:**
```json
{
  "news_articles": [
    {
      "headline": "Cashew prices expected to rise 3-5% in December",
      "source": "AgriTrade",
      "date": "Dec 24, 2025",
      "url": null
    }
  ]
}
```

---

## 📊 Données Stockées en DB

**Table:** `market_trends`

**Nouveaux champs:**
```sql
-- Tweets
top_tweets: JSONB[]  -- Array de tweets avec metadata
tweet_count: INTEGER  -- Nombre de tweets trouvés

-- News (NEW)
news_articles: JSONB[]  -- Array d'articles avec metadata
news_summary: TEXT  -- Résumé des articles

-- Existing
twitter_sentiment: VARCHAR
twitter_volume: INTEGER
twitter_summary: TEXT
stock_price_usd: DECIMAL
market_summary: TEXT
overall_trend: VARCHAR
confidence_score: DECIMAL
ai_analysis: TEXT  -- Analyse complète Perplexity
key_factors: TEXT[]
perplexity_citations: TEXT[]
```

---

## 🧪 Test

**Commande:**
```bash
curl -X POST "http://localhost:8000/api/v1/trends/analyze/cashew?force_refresh=true"
```

**Attendu:**
```json
{
  "status": "success",
  "data": {
    "commodity": "cashew",
    "tweet_count": 5,  // ≥5 tweets
    "top_tweets": [
      {
        "text": "Vietnam cashew exports up 15%...",
        "username": "AgriTradeNews",
        "created_at": "Dec 26, 2025"
      }
      // ... 4 autres tweets
    ],
    "news_articles": [
      {
        "headline": "Global cashew demand rises...",
        "source": "CommodityNews",
        "date": "Dec 25, 2025"
      }
      // ... 2-4 autres articles
    ],
    "twitter_sentiment": "bullish",
    "overall_trend": "bullish",
    "confidence_score": 0.75,  // Plus haut car 3 sources convergent
    "ai_analysis": "Full comprehensive analysis..."
  }
}
```

---

## ⚠️ Limitations Connues

### 1. Perplexity Peut Ne Pas Trouver de Tweets

**Raisons:**
- Twitter a limité l'accès API en 2023
- Perplexity utilise sources secondaires (articles mentionnant des tweets)
- Peu de volume Twitter sur marché B2B du cajou

**Stratégie de fallback dans le prompt:**
- Si 0 tweets cashew → chercher "agriculture commodities"
- Si 0 tweets → chercher "Vietnam Cambodia exports"
- Si 0 tweets → chercher "food trade" général

**Résultat pire cas:**
- Tweets génériques sur agriculture
- Mieux que 0 tweets
- Analyse fonctionne quand même avec articles + prix

---

### 2. Qualité Articles > Tweets

Pour un marché B2B comme le cajou:
- ✅ Articles trade publications = très fiables
- ✅ Rapports FAO/World Bank = authoritative
- ⚠️ Tweets = anecdotiques, moins fiables

**Notre approche:** Utiliser les 3 sources et cross-référencer

---

### 3. Cache 24h

**Problème:** Les nouvelles analyses sont cachées 24h

**Solutions:**
1. Force refresh: `?force_refresh=true`
2. Attendre 24h
3. Supprimer entrée DB manuellement

---

## 📝 Fichiers Modifiés

| Fichier | Lignes | Modification |
|---------|--------|--------------|
| `app/services/perplexity_service.py` | 377-507 | Prompt complet 3 sources + fallback |
| `app/services/market_trends_service.py` | 87-96 | Ajout champs news_articles |
| `app/services/market_trends_service.py` | 237-273 | Parsing articles + summaries |

---

## ✅ Checklist Déploiement

- ✅ Prompt Perplexity renforcé (MANDATORY keywords)
- ✅ Section NEWS ajoutée
- ✅ Parsing tweets amélioré (dict + metadata)
- ✅ Parsing articles implémenté (nouveau)
- ✅ Champs DB ajoutés (news_articles, tweet_count)
- ✅ API redémarrée
- ⏳ **Test avec force_refresh** (à faire)

---

## 🚀 Prochaines Étapes

**Immédiat:**
1. Lancer test: `curl -X POST "http://localhost:8000/api/v1/trends/analyze/cashew?force_refresh=true"`
2. Attendre 30-60 secondes (Perplexity call)
3. Vérifier résultat:
   - `tweet_count` ≥ 5 ?
   - `news_articles` ≥ 3 ?
   - `overall_trend` basé sur 3 sources ?

**Si échec:**
- Lire `ai_analysis` complet pour voir ce que Perplexity a trouvé
- Ajuster prompt si pattern pas respecté
- Vérifier logs API pour erreurs

**Si succès:**
- ✅ UI Scenario Analysis affichera 5 tweets + articles
- ✅ Analyse plus riche et fiable
- ✅ Confidence score plus élevé (3 sources)

---

**Implémenté par:** Claude Code
**Date:** 2025-12-27 22:45
**Status:** ✅ PRÊT À TESTER

**Commande de test:**
```bash
curl -X POST "http://localhost:8000/api/v1/trends/analyze/cashew?force_refresh=true" \
  -H "Content-Type: application/json" \
  | python -m json.tool
```

**Durée attendue:** 30-60 secondes (Perplexity AI call)
