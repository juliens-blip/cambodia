# Amélioration: Recherche de Tweets Élargie

**Date:** 2025-12-27 22:30
**Status:** ✅ IMPLÉMENTÉ

---

## 🎯 Objectif

Modifier le prompt Perplexity pour chercher les **5 derniers tweets** sur le marché GLOBAL du cajou (au lieu de seulement Cambodia-specific) pour enrichir les analyses.

---

## ✅ Modifications Appliquées

### 1. Prompt Perplexity Élargi

**Fichier:** `app/services/perplexity_service.py` (lignes 384-403)

**AVANT (trop restrictif):**
```python
1. TWITTER/X ANALYSIS (Last 48 hours):
   - Search Twitter/X for recent tweets about '{commodity}' market, prices, exports
   - Identify sentiment (bullish/bearish/neutral)
   - Count relevant tweet volume
   - Extract 3-5 most influential tweets with author info
   - Focus on: traders, exporters, commodity analysts, market news
```

**Problème:** Cherche seulement Cambodia + 48h = 0 résultats

---

**APRÈS (global + structuré):**
```python
1. TWITTER/X ANALYSIS (Last 7 days):
   - Search Twitter/X for the 5 most recent tweets about GLOBAL '{commodity}' market
   - Include: Southeast Asia (Vietnam, Cambodia, Thailand), India, Africa, global markets
   - Focus on: market prices, trade flows, exports, industry news
   - For EACH of the 5 tweets, extract and format EXACTLY like this:

     Tweet 1: "Full tweet text here" - @username (Date)
     Tweet 2: "Full tweet text here" - @username (Date)
     Tweet 3: "Full tweet text here" - @username (Date)
     Tweet 4: "Full tweet text here" - @username (Date)
     Tweet 5: "Full tweet text here" - @username (Date)

   - Identify overall sentiment (bullish/bearish/neutral)
   - Count total relevant tweet volume
   - Summarize key themes and market concerns
```

**Améliorations:**
- ✅ **Recherche élargie**: Global cashew market (Vietnam, India, Africa, etc.)
- ✅ **Fenêtre plus large**: 7 jours au lieu de 48h
- ✅ **Format structuré**: Demande explicite d'extraire @username et date
- ✅ **5 tweets explicites**: Numérotés pour forcer l'extraction

---

### 2. Parsing Amélioré des Tweets

**Fichier:** `app/services/market_trends_service.py` (lignes 200-230)

**AVANT (basique):**
```python
# Extract top tweets (look for quoted text or @mentions)
tweets = []
tweet_pattern = r'"([^"]{20,200})"'
tweet_matches = re.findall(tweet_pattern, response_text)
tweets.extend(tweet_matches[:5])

parsed['top_tweets'] = tweets  # Liste de strings
```

**Problème:**
- Regex trop simple (max 200 chars, tweets font 280)
- Retourne des strings simples
- Pas d'extraction de métadonnées

---

**APRÈS (robuste avec métadonnées):**
```python
# Extract top tweets (improved parsing for new format)
tweets = []

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
        'likes': 0,  # Not available from Perplexity
        'retweets': 0
    })

# Pattern 2: Fallback to quoted text (old format)
if len(tweets) == 0:
    tweet_pattern_old = r'"([^"]{20,280})"'
    tweet_matches = re.findall(tweet_pattern_old, response_text)
    for tweet_text in tweet_matches[:5]:
        tweets.append({
            'text': tweet_text,
            'username': 'unknown',
            'created_at': 'N/A',
            'likes': 0,
            'retweets': 0
        })

parsed['top_tweets'] = tweets[:5]  # Max 5 tweets, format dict
```

**Améliorations:**
- ✅ **Regex robuste**: Capture jusqu'à 280 caractères
- ✅ **Extraction métadonnées**: username, date
- ✅ **Format dict**: Compatible avec UI existante
- ✅ **Fallback**: Si nouveau format échoue, utilise l'ancien
- ✅ **Max 5 tweets**: Limite explicite

---

## 🧪 Comment Tester

### Option 1: Forcer Nouvelle Analyse

**Via API:**
```bash
curl -X POST "http://localhost:8000/api/v1/trends/analyze/cashew?force_refresh=true"
```

**Résultat attendu:**
```json
{
  "status": "success",
  "data": {
    "commodity": "cashew",
    "top_tweets": [
      {
        "text": "Vietnam cashew exports surge 15% in Q4 2025...",
        "username": "AgriTradeNews",
        "created_at": "Dec 26, 2025",
        "likes": 0,
        "retweets": 0
      },
      // ... 4 autres tweets
    ],
    "twitter_volume": 127,
    "twitter_sentiment": "bullish"
  }
}
```

---

### Option 2: Via UI Scenario Analysis

**Important:** Vider le cache d'abord !

```bash
# Option A: Vider cache Streamlit
# Dans l'UI, cliquer sur "🔄 Refresh Analysis" dans la sidebar

# Option B: Vider cache API (base de données)
curl -X DELETE "http://localhost:8000/api/v1/cache/clear"  # Si endpoint existe

# Option C: Attendre 24h (TTL du cache)
```

**Puis:**
1. Ouvrir http://localhost:8501/Scenario_Analysis
2. Sélectionner "Cashew"
3. Cliquer sur "🔄 Refresh Analysis" (sidebar)
4. Attendre génération (~30-60 secondes)
5. Vérifier section "🐦 Key Tweet"

**Résultat attendu:**
```
🐦 Key Tweet

┌─────────────────────────────────────────────┐
│ @AgriTradeNews                               │
│                                              │
│ Vietnam cashew exports surge 15% in Q4 2025 │
│ as global demand from US and Europe rises.  │
│ Prices expected to stabilize around $1,500  │
│ per ton for raw cashew nuts.                │
│                                              │
│ ❤️ 0 • 🔄 0 • Dec 26, 2025                   │
└─────────────────────────────────────────────┘
```

---

## 📊 Différences Attendues

### AVANT (0 tweets)
```
📊 Data Sources
┌─────────────┬──────────────────┬──────────────┐
│ Market Data │ Historical Docs  │ Twitter/X    │
│ $8,500/ton  │ 5 documents      │ 0 tweets  ❌ │
│ +7.87%      │ analyzed         │              │
└─────────────┴──────────────────┴──────────────┘

ℹ️ No recent tweets found. Analysis will focus on market
   data and historical documents.
```

---

### APRÈS (5 tweets attendus)
```
📊 Data Sources
┌─────────────┬──────────────────┬──────────────┐
│ Market Data │ Historical Docs  │ Twitter/X    │
│ $8,500/ton  │ 5 documents      │ 5 tweets  ✅ │
│ +7.87%      │ analyzed         │              │
└─────────────┴──────────────────┴──────────────┘

🐦 Key Tweet

@AgriTradeNews
Vietnam cashew exports surge 15% in Q4 2025...
❤️ 0 • 🔄  0 • Dec 26, 2025
```

---

## ⚠️ Limitations Connues

### 1. Pas de Métriques d'Engagement

**Problème:** Perplexity ne fournit pas likes/retweets

**Solution actuelle:** Hardcodé à 0

**Amélioration possible:**
- Utiliser Twitter API directement (nécessite credentials)
- Afficher seulement si > 0

---

### 2. Cache API (24h TTL)

**Problème:** Les analyses sont cachées 24h

**Impact:** Nouveau prompt ne s'applique pas aux anciennes analyses

**Solutions:**
1. **Attendre 24h** pour voir nouveaux tweets
2. **Force refresh** via `force_refresh=true`
3. **Vider cache manuellement** (DB query)

---

### 3. Fiabilité Perplexity

**Problème:** Perplexity peut ne pas toujours trouver des tweets récents

**Raisons possibles:**
- Sources limitées
- Tweets non indexés
- Délai d'indexation

**Fallback:** L'analyse fonctionne quand même avec prix + documents

---

## 🔧 Dépannage

### Problème: Toujours 0 tweets après modification

**Causes possibles:**

1. **Cache actif**
   ```bash
   # Vérifier l'âge du cache
   curl "http://localhost:8000/api/v1/trends/latest/cashew" | grep trend_date

   # Si trend_date < aujourd'hui, c'est du cache
   # Solution: Force refresh
   curl -X POST "http://localhost:8000/api/v1/trends/analyze/cashew?force_refresh=true"
   ```

2. **API pas redémarrée**
   ```bash
   # Vérifier l'uptime
   ps aux | grep uvicorn

   # Si >30 minutes, redémarrer
   taskkill //F //IM python.exe
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Perplexity ne trouve vraiment pas de tweets**
   ```bash
   # Tester manuellement sur perplexity.ai
   # Query: "Find the 5 most recent tweets about global cashew market in the last 7 days"

   # Si Perplexity web ne trouve pas non plus, c'est normal
   ```

---

### Problème: Format de tweet incorrect

**Symptôme:** Tweets affichent "unknown" comme username

**Cause:** Regex ne match pas le format Perplexity

**Debug:**
```python
# Lire la réponse brute Perplexity
curl "http://localhost:8000/api/v1/trends/latest/cashew" | grep -A 50 "TWITTER"

# Voir le format exact des tweets dans ai_analysis
# Puis ajuster le regex dans market_trends_service.py ligne 204
```

---

## 📝 Fichiers Modifiés

| Fichier | Lignes | Changement |
|---------|--------|------------|
| `app/services/perplexity_service.py` | 384-403 | Prompt Twitter élargi (global + 7 jours) |
| `app/services/market_trends_service.py` | 200-230 | Parsing amélioré (dict + métadonnées) |

---

## ✅ Checklist Déploiement

- ✅ Prompt Perplexity modifié
- ✅ Parsing tweets amélioré
- ✅ API redémarrée
- ✅ Streamlit redémarré (déjà running)
- ⏳ **Test avec force_refresh** (à faire)
- ⏳ **Vérification tweets affichés** (à faire par user)

---

## 🚀 Prochaines Étapes

**Immédiat:**
1. Tester avec force refresh
2. Vérifier si tweets trouvés
3. Valider affichage UI

**Si toujours 0 tweets:**
- Tester query sur perplexity.ai web
- Ajuster prompt si nécessaire
- Considérer Twitter API directe

**Si tweets trouvés:**
- ✅ Fonctionnalité complète
- Documenter exemples de tweets
- Monitorer qualité sur 1 semaine

---

**Implémenté par:** Claude Code
**Date:** 2025-12-27 22:30
**Status:** ✅ PRÊT À TESTER

**Action requise:** Force refresh pour voir les nouveaux tweets
