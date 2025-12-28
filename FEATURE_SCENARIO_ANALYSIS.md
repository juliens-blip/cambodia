# Feature: Analyses Multi-Perspectives (Scenario Analysis)

**Date:** 2025-12-27
**Status:** ✅ IMPLÉMENTÉ

---

## 🎯 Description

Nouvelle page d'analyse qui génère **3 scénarios différents** pour le marché du cajou et du caoutchouc :

1. **📉 Analyse Dépréciative (Pessimiste)**
   - Scénario baissier avec facteurs de risque
   - Focus sur les menaces et risques de baisse des prix
   - Perspective conservatrice

2. **⚖️ Analyse Réaliste (Neutre)**
   - Vue équilibrée basée sur les données
   - Scénario le plus probable
   - Approche objective

3. **📈 Analyse Positive (Optimiste)**
   - Scénario haussier avec opportunités
   - Focus sur les catalyseurs de croissance
   - Perspective optimiste

---

## 📊 Sources de Données

Chaque analyse s'appuie sur **3 sources de données** :

### 1. Prix du Marché 💰
- **API:** `/api/v1/trends/public/prices/{commodity}?days={days}`
- **Données:** Prix historiques (USD/tonne)
- **Statistiques:** Prix actuel, moyen, max, min, variation %

### 2. Documentation Historique 📚
- **API:** `/api/v1/semantic/search`
- **Données:** Documents PDF pertinents de la base de données
- **Nombre:** 5 documents les plus pertinents
- **Contenu:** Analyses historiques, rapports de marché

### 3. Actualités Twitter/X 🐦
- **API:** `/api/v1/trends/latest/{commodity}`
- **Données:** Sentiment Twitter, tweets récents
- **Contenu:** Top tweets, volume de tweets (48h)
- **Affichage:** Tweet le plus pertinent mis en avant

---

## 🤖 Génération des Analyses

### Méthode
Chaque scénario est généré via **Perplexity AI** (RAG endpoint) avec des prompts spécifiques :

**Analyse Dépréciative:**
```
As a conservative market analyst, provide a PESSIMISTIC (bearish) analysis...
Focus on:
1. Price Outlook: Downside risks, potential price declines
2. Risk Factors: Supply gluts, demand weakness, market headwinds
3. Bearish Scenarios: What could go wrong in the next 3-6 months
```

**Analyse Réaliste:**
```
As a balanced market analyst, provide a REALISTIC (neutral) analysis...
Focus on:
1. Price Outlook: Most likely price trajectory based on fundamentals
2. Balanced View: Both upside and downside factors
3. Probable Scenarios: What's most likely in the next 3-6 months
```

**Analyse Positive:**
```
As an opportunity-focused market analyst, provide an OPTIMISTIC (bullish) analysis...
Focus on:
1. Price Outlook: Upside potential, bullish catalysts
2. Opportunities: Strong demand drivers, supply constraints, growth factors
3. Bullish Scenarios: What could drive prices higher in the next 3-6 months
```

### Caching
- **TTL:** 1 heure (3600 secondes)
- **Cache clés:** Données marché, documents, Twitter
- **Refresh:** Bouton "🔄 Rafraîchir l'analyse"

---

## 🖥️ Interface Utilisateur

### Structure de la Page

```
📊 Analyses Multi-Perspectives
3 scénarios basés sur les prix du marché, documents historiques et actualités Twitter/X

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📊 Sources de Données

[Prix Actuel]      [Documents]      [Tweets]
$8,500/ton        5 documents      25 tweets
+1.80%            analyzed         recent

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🐦 Tweet Clé

┌──────────────────────────────────────┐
│ @username                             │
│ Tweet content here...                 │
│ ❤️ 123 • 🔄 45 • 2025-12-27          │
└──────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[📉 Analyse Dépréciative] [⚖️ Analyse Réaliste] [📈 Analyse Positive]

[Contenu de l'analyse sélectionnée]

📚 Sources & Citations (3)
  [1] Document content...
  [2] Document content...
  [3] Document content...
```

### Paramètres (Sidebar)

- **Matière première:** Cajou / Caoutchouc
- **Historique (jours):** 7 - 90 jours (défaut: 30)
- **Bouton:** 🔄 Rafraîchir l'analyse

### Informations

**En français:**
```
### À propos

Cette page génère 3 analyses différentes :

- 📉 Dépréciative: Scénario pessimiste avec facteurs de risque
- ⚖️ Réaliste: Vue équilibrée basée sur les données
- 📈 Positive: Scénario optimiste avec opportunités

Chaque analyse utilise :
- Prix du marché en temps réel
- Documents historiques pertinents
- Sentiment Twitter/X récent
- IA Perplexity pour génération
```

---

## 🧪 Comment Tester

### 1. Accéder à la Page

1. **Ouvrir:** http://localhost:8501
2. **Sélectionner langue:** 🇫🇷 Français (sidebar)
3. **Naviguer:** Cliquer sur "📊 Scenario Analysis" dans le menu

### 2. Sélectionner une Matière Première

- Choisir **Cajou** ou **Caoutchouc**
- Ajuster l'historique (7-90 jours)

### 3. Consulter les Sources

Vérifier l'affichage :
- ✅ Prix actuel du marché
- ✅ Nombre de documents analysés
- ✅ Nombre de tweets récents

### 4. Voir le Tweet Clé

- ✅ Tweet le plus pertinent affiché
- ✅ Informations: username, likes, retweets, date

### 5. Explorer les 3 Scénarios

**Onglet 1 - 📉 Dépréciative:**
- Analyse pessimiste générée
- Facteurs de risque mis en avant
- Sources citées en bas

**Onglet 2 - ⚖️ Réaliste:**
- Analyse équilibrée générée
- Vision objective des données
- Sources citées en bas

**Onglet 3 - 📈 Positive:**
- Analyse optimiste générée
- Opportunités mises en avant
- Sources citées en bas

### 6. Vérifier les Citations

- Cliquer sur "📚 Sources & Citations"
- Vérifier que les documents sources sont affichés

---

## 📁 Fichiers Créés/Modifiés

### Nouveaux Fichiers

**`ui/pages/6_📊_Scenario_Analysis.py`** (NEW - 400+ lignes)
- Page principale d'analyse de scénarios
- 3 onglets pour les 3 types d'analyses
- Intégration de 3 sources de données
- Génération via Perplexity AI

### Fichiers Modifiés

**`ui/i18n/translations.py`** (MODIFIED)
- Ajout de 25+ clés de traduction pour la page
- Traductions EN et FR

**Traductions ajoutées:**
```python
"fr": {
    "scenario_title": "Analyses Multi-Perspectives",
    "scenario_subtitle": "3 scénarios basés sur...",
    "scenario_pessimistic": "📉 Analyse Dépréciative",
    "scenario_realistic": "⚖️ Analyse Réaliste",
    "scenario_optimistic": "📈 Analyse Positive",
    "scenario_market_data": "Données du marché",
    "scenario_historical_docs": "Documents historiques",
    "scenario_twitter_news": "Actualités Twitter/X",
    "scenario_key_tweet": "Tweet Clé",
    # ... 15+ autres traductions
}
```

---

## 🔌 Endpoints API Utilisés

### 1. Prix Publics
```http
GET /api/v1/trends/public/prices/{commodity}?days=30
```

**Réponse:**
```json
{
  "commodity": "cashew",
  "days": 30,
  "count": 25,
  "data": [...],
  "statistics": {
    "current": 8500,
    "average": 8416.67,
    "highest": 8500,
    "lowest": 8350,
    "change_pct": 1.796
  }
}
```

### 2. Recherche Sémantique
```http
GET /api/v1/semantic/search?query=cashew market trends&limit=5&commodity_filter=cashew
```

**Réponse:**
```json
{
  "results": [
    {
      "content": "...",
      "source": "...",
      "similarity": 0.85,
      "commodity": "cashew"
    }
  ]
}
```

### 3. Données Twitter
```http
GET /api/v1/trends/latest/{commodity}
```

**Réponse:**
```json
{
  "trend_date": "2025-12-27",
  "overall_trend": "bullish",
  "twitter_sentiment": "bullish",
  "tweet_count": 25,
  "top_tweets": [
    {
      "username": "trader123",
      "text": "Cashew prices looking strong...",
      "likes": 123,
      "retweets": 45,
      "created_at": "2025-12-27T10:30:00"
    }
  ]
}
```

### 4. Génération RAG (Perplexity)
```http
POST /api/v1/semantic/rag
Content-Type: application/json

{
  "question": "As a conservative market analyst...",
  "commodity_filter": "cashew",
  "limit": 3
}
```

**Réponse:**
```json
{
  "answer": "Analysis text...",
  "citations": [...],
  "cost": 0.005
}
```

---

## 💡 Caractéristiques Techniques

### Caching
- **Fonction:** `@st.cache_data(ttl=3600)`
- **Données cachées:**
  - Prix du marché (1h)
  - Documents historiques (1h)
  - Données Twitter (1h)
  - Analyses générées (1h)

### Gestion d'Erreurs
- Try-catch sur tous les appels API
- Messages d'erreur traduits
- Fallback sur données vides si API échoue

### Performance
- Appels API en parallèle (httpx.Client)
- Spinner pendant génération
- Cache pour éviter appels répétés

### Responsive Design
- Colonnes adaptatives (st.columns)
- Tabs pour navigation entre scénarios
- Container pour tweet stylisé

---

## ✅ État de Complétion

- [x] Page créée et fonctionnelle
- [x] Traductions FR/EN ajoutées
- [x] Intégration prix du marché
- [x] Intégration documents historiques
- [x] Intégration données Twitter/X
- [x] Génération 3 scénarios via IA
- [x] Affichage tweet le plus pertinent
- [x] Citations et sources
- [x] Caching implémenté
- [x] Streamlit redémarré
- [x] Tests manuels

---

## 🎯 Prochaines Améliorations (Optionnelles)

1. **Export PDF:** Permettre d'exporter les 3 analyses en PDF
2. **Graphiques:** Ajouter des graphiques de prix dans chaque scénario
3. **Comparaison:** Vue côte-à-côte des 3 scénarios
4. **Historique:** Sauvegarder les analyses générées
5. **Notifications:** Alertes si scénario change significativement
6. **Langues:** Ajouter traductions KM et VI
7. **Customisation:** Permettre d'ajuster les prompts IA

---

## 📊 Résultat Final

**Nouvelle option dans le menu:**
```
📊 Scenario Analysis
```

**Située après:**
```
📈 Market Trends
```

**Fonctionnalités:**
- ✅ 3 analyses perspectives différentes
- ✅ Basées sur prix réels du marché
- ✅ Contexte de documents historiques
- ✅ Actualités Twitter/X intégrées
- ✅ Tweet le plus pertinent affiché
- ✅ Sources et citations pour chaque analyse
- ✅ Interface entièrement traduite (FR/EN)
- ✅ Caching pour performance

---

**Implémenté par:** Claude Code
**Date:** 2025-12-27
**Temps de développement:** ~30 minutes
**Status:** ✅ 100% FONCTIONNEL
