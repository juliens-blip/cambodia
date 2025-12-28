# BugFix: Timeout Issues - Scenario Analysis

**Date:** 2025-12-27
**Status:** ✅ CORRIGÉ

---

## 🐛 Problème

**Erreurs constatées:**
```
Error fetching documents: timed out
Error fetching Twitter data: timed out
0 documents analysés
0 tweets récents
Unable to generate pessimistic analysis. Please try again.
```

---

## 🔍 Cause Racine

Les **timeouts étaient trop courts** pour les opérations lentes:

1. **Recherche sémantique (première fois)**: 60-120 secondes
   - Chargement du modèle d'embedding (multilingual-e5-large)
   - Génération des embeddings pour la requête
   - Recherche dans la base de données

2. **Appels RAG (Perplexity AI)**: 30-60 secondes
   - Recherche contextuelle
   - Appel API externe Perplexity
   - Génération de réponse

3. **Timeouts originaux trop courts:**
   - Market data: 10s ❌
   - Documents: 15s ❌
   - Twitter: 10s ❌
   - RAG query: 30s ❌

---

## ✅ Solution Appliquée

### 1. Augmentation des Timeouts

**Fichier:** `ui/pages/6_📊_Scenario_Analysis.py`

#### Market Data
```python
# AVANT:
response = client.get(url, timeout=10.0)

# APRÈS:
response = client.get(url, timeout=30.0)
```

#### Historical Documents Search
```python
# AVANT:
response = client.post(url, json=payload, timeout=15.0)

# APRÈS:
# First search can take 60+ seconds (model loading)
response = client.post(url, json=payload, timeout=120.0)
```

#### Twitter Data
```python
# AVANT:
response = client.get(url, timeout=10.0)

# APRÈS:
response = client.get(url, timeout=30.0)
```

#### RAG Analysis Generation
```python
# AVANT:
response = client.post(url, json=payload, timeout=30.0)

# APRÈS:
# RAG query can take 30-60 seconds (Perplexity AI call + search)
response = client.post(url, json=payload, timeout=120.0)
```

---

### 2. Amélioration de la Gestion d'Erreurs

#### Erreurs Spécifiques par Type

**TimeoutException:**
```python
except httpx.TimeoutException:
    st.warning(f"⏱️ Document search timed out (model loading can take time). Try again.")
    return None
```

**404 Not Found (Twitter):**
```python
elif response.status_code == 404:
    st.info(f"ℹ️ No Twitter data available for {commodity} yet.")
    return None
```

**429 Rate Limit (RAG):**
```python
elif response.status_code == 429:
    st.warning(f"⏱️ Rate limit exceeded. Please wait a moment and try again.")
    return {
        'analysis': f"Rate limit exceeded. Please refresh the page in a few minutes.",
        'citations': [],
        'cost': 0
    }
```

#### Messages Informatifs

**Quand pas de tweets disponibles:**
```python
def display_key_tweet(twitter_data):
    if not twitter_data:
        st.info("ℹ️ No Twitter/X data available. Analysis will proceed without social media context.")
        return

    tweets = twitter_data.get('top_tweets', [])
    if not tweets or len(tweets) == 0:
        st.info("ℹ️ No recent tweets found. Analysis will focus on market data and historical documents.")
```

---

## 🧪 Tests de Vérification

### Endpoint Prix
```bash
curl "http://localhost:8000/api/v1/trends/public/prices/cashew?days=7"
```
**Résultat:** ✅ Prix actuel: $8,500/ton, 6 jours de données

### Endpoint Twitter
```bash
curl "http://localhost:8000/api/v1/trends/latest/cashew"
```
**Résultat:** ✅ 200 OK, analyse disponible (pas de tweets bruts mais analyse IA)

### Endpoint Search
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"cashew market","top_k":2,"commodity":"cashew"}'
```
**Résultat:** ✅ 2 résultats en 752ms (modèle déjà chargé)

---

## 📊 Nouveaux Timeouts (Résumé)

| Opération | Avant | Après | Raison |
|-----------|-------|-------|--------|
| Market Data | 10s | **30s** | API peut être lente |
| Document Search | 15s | **120s** | Première requête charge modèle (60s+) |
| Twitter Data | 10s | **30s** | API peut être lente |
| RAG Query | 30s | **120s** | Perplexity AI + Search = 60s+ |

---

## ⚡ Performance Attendue

### Première Utilisation
- **1ère requête search:** 60-120 secondes (chargement modèle)
- **1ère analyse RAG:** 30-60 secondes (Perplexity API)
- **Total première page:** ~2-3 minutes

### Utilisations Suivantes
- **Search (cache):** 0.5-2 secondes ✅
- **RAG (cache):** instantané si même question ✅
- **Total page:** ~10-30 secondes ✅

---

## 🎯 Comportement Attendu Maintenant

### Scénario 1: Toutes les Données Disponibles
```
📊 Sources de Données
├─ Prix: $8,500/ton (+1.8%)
├─ Documents: 5 documents analysés
└─ Tweets: 0 tweets récents

🐦 Tweet Clé
└─ ℹ️ No recent tweets found. Analysis will focus on...

📉 Analyse Dépréciative
└─ [Analyse générée par IA basée sur prix + docs]

⚖️ Analyse Réaliste
└─ [Analyse générée par IA basée sur prix + docs]

📈 Analyse Positive
└─ [Analyse générée par IA basée sur prix + docs]
```

### Scénario 2: Timeout Documentaire
```
⏱️ Document search timed out (model loading can take time). Try again.

📊 Sources de Données
├─ Prix: $8,500/ton (+1.8%)
├─ Documents: 0 documents analysés ⚠️
└─ Tweets: 0 tweets récents

└─ Analyses générées avec contexte limité (prix seulement)
```

### Scénario 3: Rate Limit
```
⏱️ Rate limit exceeded. Please wait a moment and try again.

📉 Analyse Dépréciative
└─ Rate limit exceeded. Please refresh the page in a few minutes.
```

---

## ✅ Changements Appliqués

**Fichier modifié:** `ui/pages/6_📊_Scenario_Analysis.py`

- ✅ Lignes 58: Market data timeout 10s → 30s
- ✅ Lignes 62-65: Gestion TimeoutException pour market data
- ✅ Lignes 82: Documents timeout 15s → 120s
- ✅ Lignes 85-89: Gestion TimeoutException pour documents
- ✅ Lignes 99: Twitter timeout 10s → 30s
- ✅ Lignes 102-109: Gestion 404 + TimeoutException pour Twitter
- ✅ Lignes 205: RAG timeout 30s → 120s
- ✅ Lignes 214-227: Gestion 429 + TimeoutException pour RAG
- ✅ Lignes 268-292: Messages informatifs quand pas de tweets

---

## 🚀 Services Actifs

- ✅ **API Backend:** http://localhost:8000 (healthy)
- ✅ **Streamlit UI:** http://localhost:8501 (running)
- ✅ **Rate Limiter:** 50 req/h, 500 req/day, 5000 req/month

---

## 📋 Prochaines Actions

1. **Redémarrer Streamlit** pour appliquer les changements
2. **Tester la page** Scenario Analysis
3. **Attendre 2-3 min** pour la première analyse (normal)
4. **Vérifier cache** - deuxième visite devrait être rapide

---

**Corrigé par:** Claude Code
**Date:** 2025-12-27
**Status:** ✅ PRÊT À TESTER
