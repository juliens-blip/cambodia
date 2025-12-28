# STRATÉGIE D'INTÉGRATION MCP - CAMBODIA AGRI ANALYTICS

## MCP DISPONIBLES (5 + 1 À AJOUTER)

### ✅ MCP CONFIGURÉS

#### 1. **context7** (Upstash Context7)
```json
"context7": {
  "command": "npx",
  "args": ["-y", "@upstash/context7-mcp"]
}
```
**Usage** : Stockage contexte long-terme, mémorisation sessions
**Pour le projet** :
- Stocker contexte analyses Perplexity entre runs
- Mémoriser patterns prix détectés
- Cache intelligent multi-sessions

---

#### 2. **fetch** (HTTP Fetch Server)
```json
"fetch": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-fetch"]
}
```
**Usage** : Requêtes HTTP, scraping APIs
**Pour le projet** :
- Scraper MEF Cambodia API
- Requêtes WITS World Bank
- Appels Perplexity API
- Download Google Drive files

---

#### 3. **supabase** (Supabase Integration)
```json
"supabase": {
  "command": "npx",
  "args": ["-y", "@supabase/mcp-server-supabase@latest", "--read-only", "--project-ref=xqfozbocgyrelznccweh"],
  "env": {
    "SUPABASE_ACCESS_TOKEN": "<from MEMOIRE_CLAUDE.md>"
  }
}
```
**Usage** : Queries Supabase directes
**Pour le projet** :
- Requêtes rapides dashboard (via MCP plutôt que Python SDK)
- Inspection données debug
- Tests requêtes complexes

---

#### 4. **browsermcp** (Browser Automation)
```json
"browsermcp": {
  "command": "npx",
  "args": ["@browsermcp/mcp@latest"]
}
```
**Usage** : Scraping sites dynamiques (JavaScript)
**Pour le projet** :
- Open Development Cambodia (si JavaScript rendering nécessaire)
- Sites avec lazy loading
- Alternative à Playwright si besoin léger

---

#### 5. **executeautomation-playwright-server** (Playwright)
```json
"executeautomation-playwright-server": {
  "command": "npx",
  "args": ["-y", "@executeautomation/playwright-mcp-server"]
}
```
**Usage** : Automation navigateur avancée, tests E2E
**Pour le projet** :
- Tests E2E dashboard Streamlit
- Scraping ODC complexe si nécessaire
- Screenshots rapports automatiques

---

### 🆕 MCP À AJOUTER

#### 6. **ChromaDB** (Vector Database)
```json
"chroma": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-chroma"],
  "env": {
    "CHROMA_HOST": "localhost",
    "CHROMA_PORT": "8000"
  }
}
```
**Usage** : Recherche sémantique, embeddings
**Pour le projet** :
- **CRITIQUE** : Stocker PDFs Google Drive (cashew/rubber docs)
- Recherche sémantique multi-langue (EN/Khmer)
- Archive analyses Perplexity (search by topic)
- Rapports Claude (semantic retrieval)
- Prix contextuels (find similar market conditions)

---

## STRATÉGIE CHROMADB (5 COLLECTIONS)

### Collection 1 : `commodity_documents`
**Purpose** : Repository PDFs/KML Google Drive

**Schema** :
```python
{
  "id": "uuid",
  "document": "text content (OCR khmer → english)",
  "metadata": {
    "commodity": "cashew" | "rubber",
    "source_file": "filename.pdf",
    "language": "khmer" | "english",
    "upload_date": "2024-01-01",
    "file_type": "pdf" | "kml",
    "geolocation": {"lat": 12.5, "lon": 104.9}  # si KML
  },
  "embedding": [0.1, 0.2, ...]  # auto-generated
}
```

**Queries** :
```python
# Recherche docs cashew en khmer
results = collection.query(
  query_texts=["cashew production techniques"],
  where={"commodity": "cashew", "language": "khmer"},
  n_results=5
)

# Find similar geospatial data
results = collection.query(
  query_texts=["Kampong Cham province"],
  where={"file_type": "kml"},
  n_results=10
)
```

---

### Collection 2 : `perplexity_analyses`
**Purpose** : Archive recherches Perplexity avec citations

**Schema** :
```python
{
  "id": "uuid",
  "document": "Perplexity response text",
  "metadata": {
    "commodity": "cashew" | "rubber",
    "query_type": "price" | "geopolitics" | "market_trends",
    "query_date": "2024-01-01T06:00:00Z",
    "citations": [{"url": "...", "title": "..."}],
    "keywords": ["Vietnam", "processing", "export"]
  }
}
```

**Queries** :
```python
# Find analyses on Vietnam processing
results = collection.query(
  query_texts=["Vietnam cashew processing industry"],
  where={"commodity": "cashew"},
  n_results=3
)

# Historical geopolitical analyses
results = collection.query(
  query_texts=["US-China trade war impact"],
  where={"query_type": "geopolitics"},
  n_results=10
)
```

---

### Collection 3 : `claude_reports`
**Purpose** : Archive rapports générés (daily/weekly)

**Schema** :
```python
{
  "id": "uuid",
  "document": "Full markdown report content",
  "metadata": {
    "commodity": "cashew" | "rubber",
    "report_type": "daily" | "weekly" | "crisis",
    "created_at": "2024-01-01T06:30:00Z",
    "insights": ["key insight 1", "key insight 2"],
    "price_range_usd": {"min": 2000, "max": 2500},
    "sentiment": "bullish" | "bearish" | "neutral"
  }
}
```

**Queries** :
```python
# Find similar market conditions
results = collection.query(
  query_texts=["price drop due to oversupply"],
  where={"commodity": "rubber", "sentiment": "bearish"},
  n_results=5
)

# Historical crisis reports
results = collection.query(
  query_texts=["export ban Vietnam"],
  where={"report_type": "crisis"},
  n_results=3
)
```

---

### Collection 4 : `commodity_prices`
**Purpose** : Prix avec contexte sémantique

**Schema** :
```python
{
  "id": "uuid",
  "document": "Context: Price $2450/ton on 2024-01-15, Vietnam demand high, China processing delays",
  "metadata": {
    "commodity": "cashew",
    "date": "2024-01-15",
    "price_usd": 2450,
    "volume_tons": 1200,
    "destination": "Vietnam",
    "quality_grade": "W320",
    "market_conditions": ["high_demand", "supply_shortage"]
  }
}
```

**Queries** :
```python
# Find similar price scenarios
results = collection.query(
  query_texts=["high Vietnam demand with supply constraints"],
  where={"commodity": "cashew"},
  n_results=10
)

# Price forecast training data
results = collection.query(
  query_texts=["$2400-2600 price range W320 grade"],
  where={"quality_grade": "W320"},
  n_results=20
)
```

---

### Collection 5 : `production_data`
**Purpose** : Données production avec géospatial

**Schema** :
```python
{
  "id": "uuid",
  "document": "Kampong Cham: 5000 hectares cashew, yield 800kg/ha, production increased 15% YoY",
  "metadata": {
    "commodity": "cashew",
    "province": "Kampong Cham",
    "year": 2023,
    "area_hectares": 5000,
    "production_tons": 4000,
    "yield_kg_per_ha": 800,
    "geolocation": {"lat": 12.5, "lon": 105.4}
  }
}
```

**Queries** :
```python
# Find high-yield regions
results = collection.query(
  query_texts=["high productivity regions above 900kg per hectare"],
  where={"commodity": "rubber"},
  n_results=5
)

# Year-over-year growth analysis
results = collection.query(
  query_texts=["production growth trends 2020-2024"],
  n_results=15
)
```

---

## INTÉGRATION WORKFLOW

### Workflow 1 : Data Collection → ChromaDB
```python
# Collector finishes
data = mef_collector.collect()

# Store in Supabase (structured)
supabase.insert("prices", data)

# ALSO store in ChromaDB (semantic search)
chroma_prices.add(
  documents=[f"Price ${d['price']} on {d['date']} to {d['destination']}"],
  metadatas=[d],
  ids=[d['id']]
)
```

### Workflow 2 : Perplexity → ChromaDB → Claude
```python
# Perplexity research
analysis = perplexity.research("cashew Vietnam processing")

# Store in ChromaDB
chroma_analyses.add(
  documents=[analysis.response],
  metadatas=[{"query_date": now(), "citations": analysis.citations}]
)

# Claude retrieves context from ChromaDB
context = chroma_analyses.query("Vietnam processing trends", n_results=5)
report = claude.generate_report(data + context)

# Store report in ChromaDB
chroma_reports.add(documents=[report.content], metadatas=[report.metadata])
```

### Workflow 3 : Dashboard Query → ChromaDB
```python
# User searches in dashboard
user_query = "Why did cashew prices spike in June 2024?"

# Semantic search across all collections
price_context = chroma_prices.query(user_query, n_results=5)
analysis_context = chroma_analyses.query(user_query, n_results=3)
report_context = chroma_reports.query(user_query, n_results=2)

# Display comprehensive answer
dashboard.show_answer(price_context + analysis_context + report_context)
```

---

## CHROMADB SETUP SCRIPT

### Installation
```bash
# Docker (recommended)
docker run -d -p 8000:8000 chromadb/chroma

# OU Python local
pip install chromadb
# Then in Python:
import chromadb
client = chromadb.Client()
```

### Initialization Script
```python
# scripts/init_chromadb.py
import chromadb
from chromadb.config import Settings

# Connect to ChromaDB
client = chromadb.HttpClient(host="localhost", port=8000)

# Create collections
commodity_docs = client.create_collection(
    name="commodity_documents",
    metadata={"description": "PDF/KML documents from Google Drive"}
)

perplexity_analyses = client.create_collection(
    name="perplexity_analyses",
    metadata={"description": "Perplexity research results with citations"}
)

claude_reports = client.create_collection(
    name="claude_reports",
    metadata={"description": "Generated market reports (daily/weekly)"}
)

commodity_prices = client.create_collection(
    name="commodity_prices",
    metadata={"description": "Price data with market context"}
)

production_data = client.create_collection(
    name="production_data",
    metadata={"description": "Agricultural production statistics"}
)

print("✅ All ChromaDB collections created successfully")
```

---

## AVANTAGES CHROMADB POUR LE PROJET

### 1. Recherche Multi-Langue
- PDFs en khmer → embeddings multilingues
- Queries EN/KH fonctionnent ensemble
- OCR imparfait compensé par semantic similarity

### 2. Contexte Enrichi pour Claude
- Au lieu de passer juste prix bruts, on passe contexte sémantique
- "Similar situations in the past" = better insights
- Réduit tokens Claude (smart filtering)

### 3. Dashboard Intelligent
- User ask "Why?" → ChromaDB trouve contexte automatiquement
- Pas besoin SQL complexe, juste semantic search
- Combine structured (Supabase) + unstructured (ChromaDB)

### 4. Évolutivité
- Nouvelle commodity (pepper) → juste add to collections
- Nouvelle source data → add to `commodity_documents`
- Scale horizontal ChromaDB si >1M docs

### 5. Coût Perplexity Réduit
- Cache sémantique : similar query → cached result
- Au lieu de 1000 req/mois, peut-être 300 (70% cache hit)
- ROI: $20/mois saved vs $0 ChromaDB hosting local

---

## PLAN D'ACTION CHROMADB

### Étape 1 : Setup (Jour 1)
- [ ] Install ChromaDB (Docker ou pip)
- [ ] Test connexion MCP
- [ ] Run init script (5 collections)
- [ ] Validate embedding model (multilingual)

### Étape 2 : Integration (Jour 2-3)
- [ ] Modify collectors → dual write (Supabase + ChromaDB)
- [ ] Perplexity service → ChromaDB caching
- [ ] Claude service → ChromaDB context retrieval
- [ ] Dashboard → ChromaDB search widget

### Étape 3 : Migration (Jour 4)
- [ ] Import existing Google Drive PDFs
- [ ] OCR khmer → embeddings
- [ ] Validate search quality
- [ ] Tune chunking strategy if needed

### Étape 4 : Optimization (Semaine 2)
- [ ] Benchmark query performance
- [ ] Implement metadata filtering optimization
- [ ] Add caching layer (Redis) si nécessaire
- [ ] Monitor embedding quality

---

## MÉTRIQUES DE SUCCÈS

**Semaine 1** :
- ✅ 5 collections créées et testées
- ✅ >100 documents ingérés (Google Drive PDFs)
- ✅ Search latency <500ms

**Semaine 2** :
- ✅ Dashboard search widget fonctionnel
- ✅ Claude context retrieval >70% relevance
- ✅ Perplexity cache hit rate >50%

**Semaine 4** :
- ✅ >1000 documents indexés
- ✅ Multi-commodity search working
- ✅ User satisfaction >80% (semantic search relevance)

---

**ChromaDB = INTELLIGENCE LAYER du projet** 🧠
