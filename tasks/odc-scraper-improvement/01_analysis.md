# Analyse: Amélioration ODC Scraper

## 📋 Contexte
**Date:** 2025-12-25
**Demande initiale:** Améliorer le ODC collector pour scraper les vraies données au lieu de générer des samples
**Objectif:** Passer de 30 sample records à 150-200 production records réels depuis Open Development Cambodia
**Priority:** HIGH (d'après audit qualité)

---

## 🔍 État Actuel de la Codebase

### Fichiers Concernés

| Fichier | Type | Rôle | Lignes |
|---------|------|------|--------|
| `app/collectors/odc_collector.py` | Collector principal | Scrape ODC + fallback samples | 316 |
| `app/config.py` | Configuration | ODC base URL config | 40 |
| `app/scheduler/jobs.py` | Orchestrateur | Lance le collector | 100 |
| `logs/test_daily_pipeline_*.log` | Logs | Erreurs 404 documentées | ~150K |

---

## 🐛 Problème Principal: URLs Retournent 404

### URLs Ciblées - Statut HTTP

Les 4 URLs hardcodées dans le collector retournent **toutes des erreurs 404**:

| URL | Statut | Vérifié le |
|-----|--------|------------|
| `https://data.opendevelopmentcambodia.net/en/dataset/cashew-production-statistics` | **404 NOT FOUND** | 2025-12-25 22:38:48 |
| `https://data.opendevelopmentcambodia.net/en/dataset/agricultural-production-cashew` | **404 NOT FOUND** | 2025-12-25 22:38:48 |
| `https://data.opendevelopmentcambodia.net/en/dataset/rubber-production-statistics` | **404 NOT FOUND** | 2025-12-25 22:38:48 |
| `https://data.opendevelopmentcambodia.net/en/dataset/agricultural-production-rubber` | **404 NOT FOUND** | 2025-12-25 22:38:48 |

**Résultat:** Aucune ressource trouvée → Fallback automatique vers sample data

---

## 💻 Code du ODC Collector

### Configuration des URLs (lignes 31-41)

```python
self.dataset_urls = {
    "cashew": [
        "https://data.opendevelopmentcambodia.net/en/dataset/cashew-production-statistics",
        "https://data.opendevelopmentcambodia.net/en/dataset/agricultural-production-cashew"
    ],
    "rubber": [
        "https://data.opendevelopmentcambodia.net/en/dataset/rubber-production-statistics",
        "https://data.opendevelopmentcambodia.net/en/dataset/agricultural-production-rubber"
    ]
}
```

❌ **Problème:** URLs hardcodées invalides

---

### Flux de Collection (lignes 43-102)

```python
async def collect(self):
    records = []

    for commodity, urls in self.dataset_urls.items():
        for dataset_url in urls:
            try:
                response = await client.get(dataset_url, timeout=30.0)

                if response.status_code == 404:  # ← ARRÊT ICI pour toutes les URLs
                    logger.debug(f"Dataset not found: {dataset_url}")
                    continue

                # Parse HTML pour trouver CSV/JSON (jamais atteint car 404)
                html = response.text
                resource_urls = self._extract_resource_urls(html)

                # Download et parse ressources (jamais exécuté)
                for url in resource_urls:
                    data = await self._download_and_parse(url, commodity)
                    records.extend(data)

            except Exception as e:
                logger.error(f"Error scraping {dataset_url}: {e}")
                continue

    # Fallback si aucun record collecté
    if not records:
        logger.warning("No ODC data found - creating sample production records")
        records = self._create_sample_data()  # ← ACTIVÉ systématiquement

    return records
```

**Flux actuel:**
```
4 URLs → 4× 404 → Boucle vide → if not records: TRUE → Sample data généré
```

---

### Génération de Sample Data (lignes 278-315)

```python
def _create_sample_data(self):
    provinces = ["Kampong Cham", "Kampong Thom", "Kratie", "Mondulkiri", "Ratanakiri"]
    years = [2021, 2022, 2023]
    commodities_data = {
        "cashew": {"base_production": 8000, "base_area": 15000},
        "rubber": {"base_production": 120000, "base_area": 180000}
    }

    records = []
    for commodity, data in commodities_data.items():
        for year in years:
            for province in provinces:
                records.append({
                    "commodity": commodity,
                    "year": year,
                    "province": province,
                    "production_tons": data["base_production"] * random.uniform(0.8, 1.2),
                    "area_hectares": data["base_area"] * random.uniform(0.85, 1.15),
                    "source": "ODC",
                    "metadata": {
                        "note": "Sample data - no real ODC dataset found",
                        "generated_at": datetime.utcnow().isoformat()
                    }
                })

    # Total: 2 commodities × 3 years × 5 provinces = 30 records
    return records
```

**Résultat:** 30 production records synthétiques avec des valeurs aléatoires réalistes

---

## 🔍 Parsing HTML & Extraction (lignes 126-276)

### Extraction d'URLs de Ressources (lignes 126-149)

```python
def _extract_resource_urls(self, html: str) -> List[str]:
    urls = []

    # Pattern regex pour trouver CSV/JSON/download links
    csv_pattern = r'href="([^"]*(?:\.csv|\.json|/download/[^"]+))"'
    matches = re.findall(csv_pattern, html)

    for match in matches:
        if match.startswith("http"):
            urls.append(match)
        elif match.startswith("/"):
            urls.append(f"https://data.opendevelopmentcambodia.net{match}")

    return urls[:5]  # Limite à 5 ressources max
```

❌ **Problème:** Regex simple au lieu de BeautifulSoup (fragile)
⚠️ **Limite:** Maximum 5 ressources par dataset

---

### Download & Parse Ressources (lignes 152-276)

```python
async def _download_and_parse(self, url: str, commodity: str) -> List[dict]:
    # 1. Download ressource
    response = await client.get(url)
    content = response.content

    # 2. Détecter format (JSON vs CSV)
    if url.endswith(".json") or self._is_json(content):
        return self._parse_json(content, commodity)
    else:
        return self._parse_csv(content, commodity)

def _parse_csv(self, content: bytes, commodity: str) -> List[dict]:
    # Parse flexible avec pandas
    df = pd.read_csv(io.BytesIO(content))

    # Mapping flexible de colonnes
    # (year, province, production, area, yield)
    ...

def _parse_json(self, content: bytes, commodity: str) -> List[dict]:
    # Parse JSON + extraction flexible
    ...
```

✅ **Points forts:**
- Support JSON + CSV
- Mapping flexible de colonnes
- Gestion des formats variés

❌ **Jamais exécuté** car aucune ressource trouvée (404 avant)

---

## 📚 Dépendances Utilisées

### Installées dans requirements.txt

| Librairie | Version | Usage Actuel | Usage Recommandé |
|-----------|---------|--------------|------------------|
| `httpx` | >=0.25.0 | ✅ Requêtes HTTP async | ✅ Garder |
| `beautifulsoup4` | >=4.12.0 | ❌ **Installé mais NON utilisé** | ✅ Utiliser pour parsing HTML |
| `lxml` | >=5.0.0 | ❌ Installé mais non utilisé | ✅ Parser HTML (bs4 backend) |
| `pandas` | >=2.1.0 | ✅ Parse CSV | ✅ Garder |
| `requests` | >=2.31.0 | ❌ Non utilisé (httpx préféré) | ⚠️ Optionnel |

**Opportunité:** BeautifulSoup4 est déjà installé mais le collector utilise regex au lieu de parsing HTML structuré!

---

## 📊 Logs Récents - Evidence

**Fichier:** `logs/test_daily_pipeline_20251225_223843.log`

```
2025-12-25 22:38:45,944 - INFO - Starting collection from ODC
2025-12-25 22:38:48,073 - HTTP Request: GET https://.../cashew-production-statistics "HTTP/1.1 404 NOT FOUND"
2025-12-25 22:38:48,358 - HTTP Request: GET https://.../agricultural-production-cashew "HTTP/1.1 404 NOT FOUND"
2025-12-25 22:38:48,635 - HTTP Request: GET https://.../rubber-production-statistics "HTTP/1.1 404 NOT FOUND"
2025-12-25 22:38:48,920 - HTTP Request: GET https://.../agricultural-production-rubber "HTTP/1.1 404 NOT FOUND"
2025-12-25 22:38:48,922 - WARNING - No ODC data found - creating sample production records
2025-12-25 22:38:48,923 - INFO - ODC collector found 30 production records
```

**Timeline:** 3 secondes → 4× 404 → Fallback sample data → 30 records générés

---

## ⚠️ Points d'Attention

| # | Problème | Impact | Gravité |
|---|----------|--------|---------|
| 1 | **URLs hardcodées invalides (404)** | Blocant - Pas de vrai scraping | 🔴 HIGH |
| 2 | Pas de découverte dynamique de datasets | Dépend d'URLs fixes qui cassent | 🟡 MEDIUM |
| 3 | BeautifulSoup installé mais non utilisé | Regex fragile pour parsing HTML | 🟡 MEDIUM |
| 4 | Fallback sample activé automatiquement | Masque les problèmes réels | 🟡 MEDIUM |
| 5 | Logging insuffisant (debug seulement) | Diagnostic difficile des 404 | 🟢 LOW |
| 6 | Limite 5 ressources max par dataset | Peut manquer des données | 🟢 LOW |
| 7 | Pas de gestion des redirects HTTP | Structure ODC peut changer | 🟢 LOW |

---

## 💡 Opportunités Identifiées

### 1. Découverte Dynamique de Datasets
**Opportunité:** Au lieu de hardcoder les URLs, scraper la page d'accueil ODC pour découvrir les datasets disponibles

**Approche:**
```python
# Scraper https://data.opendevelopmentcambodia.net/en/dataset
# Parser HTML avec BeautifulSoup4
# Trouver tous les datasets liés à agriculture/production
# Filtrer par keywords: "cashew", "rubber", "production", "agriculture"
```

**Avantage:** Resilient aux changements d'URLs

---

### 2. Utiliser BeautifulSoup pour Parsing Robuste
**Opportunité:** BeautifulSoup4 est déjà installé mais inutilisé

**Remplacement:**
```python
# Actuel (fragile):
matches = re.findall(r'href="([^"]*\.csv)"', html)

# Amélioré (robuste):
soup = BeautifulSoup(html, 'lxml')
links = soup.find_all('a', href=re.compile(r'\.(csv|json)$'))
urls = [link['href'] for link in links]
```

**Avantage:** Parsing HTML structuré au lieu de regex fragile

---

### 3. Recherche Multi-Sources
**Opportunité:** Plusieurs datasets ODC peuvent contenir production data

**Stratégie:**
- Search page avec query "agriculture production cambodia"
- Parse search results
- Download top 10 datasets
- Filter ceux qui contiennent commodity data

---

### 4. Parse Google Drive PDFs + KML
**Opportunité:** Le GDrive collector télécharge déjà 32 PDFs qui peuvent contenir production data

**Synergie:**
```python
# GDrive collector déjà présent
# PDFs téléchargés mais extraction échoue (pypdf issue)
# Opportunité: Fix PyPDF import → Extract tables → Merge avec ODC data
```

---

## 🔗 Dépendances & Architecture

### Dépendances Internes

```
odc_collector.py
├─ Hérite de: base_collector.BaseCollector
├─ Utilise: app.config.settings (ODC_BASE_URL)
├─ Stockage: app.services.supabase_service.upsert_production()
└─ Appelé par: app.scheduler.jobs.daily_pipeline()
```

### Dépendances Externes

```
httpx (async HTTP)
  ↓
BeautifulSoup4 + lxml (HTML parsing) ← Installés mais NON utilisés
  ↓
pandas (CSV parsing)
  ↓
Supabase (stockage)
```

---

## 📈 Impact Potentiel

### Avant (Actuel)
- **Production records:** 31 (30 sample + 1 autre source)
- **Provinces:** 5
- **Années:** 2021-2023 (3 ans)
- **Source:** Sample data synthétique
- **Quality:** "Sample data - no real ODC dataset found"

### Après (Cible)
- **Production records:** 150-200
- **Provinces:** 10-15 (expansion géographique)
- **Années:** 2015-2025 (10 ans)
- **Source:** Vraies données Open Development Cambodia
- **Quality:** Données officielles gouvernementales

**Impact:** **5-7× plus de données** + qualité améliorée

---

## 📊 Résumé Exécutif

1. **Problème principal:** Les 4 URLs ODC hardcodées retournent toutes des erreurs 404, donc aucune vraie donnée n'est collectée

2. **Fallback actif:** Le collector génère automatiquement 30 sample records quand aucune vraie donnée n'est trouvée (par design)

3. **BeautifulSoup non utilisé:** La librairie est installée mais le collector utilise regex simple au lieu de parsing HTML robuste

4. **Opportunité majeure:** Implémenter découverte dynamique de datasets au lieu de URLs hardcodées pour resilience

5. **Impact potentiel:** Passer de 30 sample records à 150-200 production records réels en scrapant activement le catalogue ODC

---

**Fichier d'analyse créé:** `tasks/odc-scraper-improvement/01_analysis.md`
**Prochaine étape:** `/plan` pour définir la stratégie d'implémentation
