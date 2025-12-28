# ⚠️ ACTION REQUISE: Migration SQL + Test

**Date:** 2025-12-27 23:00
**Status:** ⏳ EN ATTENTE ACTION UTILISATEUR

---

## 🎯 Ce Qui a Été Fait

### ✅ Prompt Perplexity Amélioré (Cambodia-Focused)

**Nouveau prompt basé sur ton feedback:**

```
PRIORITY SEARCH - Cambodia-Specific (SEARCH FIRST):
- Accounts: @KhmerTimes @PhnomPenhPost @CambodiaDaily @cambodia_news @KhNews_English
- Keywords: "Cambodia cashew" OR "Cambodian cashew" OR "cashew Cambodia"
- Hashtags: #Cambodia #CambodiaAgriculture #CambodiaExport #cashewCambodia
- Languages: English, French
- Examples: "cashew export to Jordan", "cashew processing Cambodia"

EXAMPLE (based on real tweet you found):
Tweet 1: "Cambodia exports 12 tonnes of M23 cashew nuts to Jordan for the first time,
          marking a new milestone for the Cambodian cashew industry" - @KhmerTimes (Dec 20, 2025)

SECONDARY SEARCH - Regional (if <5 tweets):
- Vietnam, India, Southeast Asia accounts
- Regional keywords

TERTIARY SEARCH - Global (fallback):
- Global commodity news
```

**Changements clés:**
- ✅ **@KhmerTimes en priorité** (ton exemple)
- ✅ **Recherche Cambodia-first** (pas global d'abord)
- ✅ **14 jours au lieu de 7** (fenêtre plus large)
- ✅ **Comptes cambodgiens spécifiques**
- ✅ **Exemple concret fourni** (export Jordan)
- ✅ **Stratégie à 3 niveaux** (Cambodia → Regional → Global)

---

## ⚠️ ACTION 1: Exécuter Migration SQL (OBLIGATOIRE)

**Problème:** La table `market_trends` n'a pas les colonnes pour stocker les articles de presse.

**Solution:** Exécute ce SQL sur ta base Supabase.

### Option A: Via Supabase Dashboard (Recommandé)

1. Va sur https://supabase.com/dashboard
2. Sélectionne ton projet Cambodia
3. Va dans **SQL Editor** (menu gauche)
4. Clique **New Query**
5. Copie-colle le SQL ci-dessous:

```sql
-- Add news articles and tweet count to market_trends table
ALTER TABLE market_trends
ADD COLUMN IF NOT EXISTS news_articles JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS news_summary TEXT DEFAULT '',
ADD COLUMN IF NOT EXISTS tweet_count INTEGER DEFAULT 0;

-- Add comments
COMMENT ON COLUMN market_trends.news_articles IS 'Array of news articles with headline, source, date, url';
COMMENT ON COLUMN market_trends.news_summary IS 'Summary of news articles analysis';
COMMENT ON COLUMN market_trends.tweet_count IS 'Number of tweets found';

-- Create index
CREATE INDEX IF NOT EXISTS idx_market_trends_tweet_count ON market_trends(tweet_count);
```

6. Clique **Run** (ou Ctrl+Enter)
7. Vérifie le message de succès

---

### Option B: Via CLI Supabase

```bash
cd D:\Projects\cambodia

# Le fichier migration existe déjà
# supabase\migrations\20251227_add_news_fields.sql

# Applique la migration
supabase db push
```

---

## ⚠️ ACTION 2: Tester le Nouveau Prompt

**Une fois le SQL exécuté**, teste l'analyse avec le nouveau prompt:

```bash
curl -X POST "http://localhost:8000/api/v1/trends/analyze/cashew?force_refresh=true" \
  -H "Content-Type: application/json" \
  | python -m json.tool > test_result.json

# Puis ouvre test_result.json
```

**Attendu avec le nouveau prompt:**

```json
{
  "status": "success",
  "data": {
    "commodity": "cashew",
    "tweet_count": 5,  // ≥1 avec le tweet @KhmerTimes sur Jordan
    "top_tweets": [
      {
        "text": "Cambodia exports 12 tonnes of M23 cashew nuts to Jordan for the first time...",
        "username": "KhmerTimes",
        "created_at": "Dec 20, 2025",
        "likes": 0,
        "retweets": 0
      },
      // ... 4 autres tweets Cambodia/Vietnam/India
    ],
    "news_articles": [
      {
        "headline": "Cambodia cashew export milestone...",
        "source": "Khmer Times",
        "date": "Dec 2025"
      }
      // ... 3-4 autres articles
    ],
    "twitter_sentiment": "bullish",  // Basé sur export success
    "overall_trend": "bullish",
    "confidence_score": 0.75,  // Plus élevé car 3 sources
    "ai_analysis": "..."
  }
}
```

---

## 📊 Différence Attendue

### AVANT (prompt global)
```
Tweet Count: 0
Top Tweets: []
Sentiment: neutral (no data)
Confidence: 0.5
```

### APRÈS (prompt Cambodia-focused)
```
Tweet Count: 5+ (including @KhmerTimes Jordan export)
Top Tweets: [
  "Cambodia exports 12 tonnes M23 cashew to Jordan..." - @KhmerTimes,
  "Vietnam cashew industry..." - @VietnamNews,
  ...
]
Sentiment: bullish (based on positive export news)
Confidence: 0.75 (3 sources aligned)
```

---

## 🧪 Vérification

**Après avoir exécuté le SQL et le test:**

1. **Vérifie les colonnes créées:**
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'market_trends'
AND column_name IN ('news_articles', 'news_summary', 'tweet_count');
```

Résultat attendu:
```
news_articles  | jsonb
news_summary   | text
tweet_count    | integer
```

2. **Vérifie les données insérées:**
```sql
SELECT
  commodity,
  trend_date,
  tweet_count,
  jsonb_array_length(news_articles) as news_count,
  twitter_sentiment,
  overall_trend
FROM market_trends
WHERE commodity = 'cashew'
ORDER BY trend_date DESC
LIMIT 1;
```

Résultat attendu:
```
cashew | 2025-12-27 | 5 | 5 | bullish | bullish
```

3. **Vérifie le contenu des tweets:**
```sql
SELECT
  top_tweets->>0 as first_tweet,
  news_articles->>0 as first_article
FROM market_trends
WHERE commodity = 'cashew'
ORDER BY trend_date DESC
LIMIT 1;
```

Devrait contenir le tweet @KhmerTimes sur Jordan.

---

## 🚀 Étapes Complètes

**Checklist:**

- [ ] **1. Exécuter SQL** (supabase dashboard ou CLI)
- [ ] **2. Vérifier colonnes créées** (query ci-dessus)
- [ ] **3. Attendre 15 secondes** (API redémarre)
- [ ] **4. Tester analyse** (`curl -X POST ...`)
- [ ] **5. Vérifier résultat**:
  - [ ] `tweet_count` ≥ 1 ?
  - [ ] `top_tweets[0]` contient @KhmerTimes ?
  - [ ] `news_articles` contient 3-5 articles ?
  - [ ] `twitter_sentiment` != neutral ?
  - [ ] `overall_trend` = bullish ?
- [ ] **6. Ouvrir UI** http://localhost:8501/Scenario_Analysis
- [ ] **7. Cliquer 🔄 Refresh Analysis**
- [ ] **8. Vérifier affichage** du tweet @KhmerTimes

---

## 📝 Fichiers Créés/Modifiés

| Fichier | Action | Description |
|---------|--------|-------------|
| `app/services/perplexity_service.py` | ✅ Modifié | Prompt Cambodia-focused avec @KhmerTimes |
| `supabase/migrations/20251227_add_news_fields.sql` | ✅ Créé | Migration SQL pour nouvelles colonnes |
| `ACTION_REQUISE_SQL_ET_TEST.md` | ✅ Créé | Ce fichier - instructions |

---

## ⏭️ Après Succès

**Si le test trouve le tweet @KhmerTimes:**

1. ✅ La fonctionnalité est **complète**
2. ✅ Analyses basées sur **4 sources** (tweets + articles + prix + docs)
3. ✅ Confidence score **élevé** (0.75+)
4. ✅ UI affichera le tweet Cambodia dans "🐦 Key Tweet"

**Si le test ne trouve TOUJOURS pas de tweets:**

Alors il faudra investiguer pourquoi Perplexity API != Perplexity Web:
- Différence d'accès Twitter entre API et Web
- Nécessité d'utiliser Twitter API directe ($100/mois)
- Ou accepter analyse sans tweets (articles + prix suffisent)

---

**Créé par:** Claude Code
**Date:** 2025-12-27 23:00
**Status:** ⏳ **EN ATTENTE: Exécute le SQL puis teste !**

**Prochaine étape:** Exécute le SQL sur Supabase Dashboard, puis lance le test.
