# Daily Pipeline - Recommandations et Roadmap

## Résumé Exécutif

### État Actuel du Pipeline

✅ **Fonctionnalités Implémentées**:
- Collecte automatisée de 4 sources de données (MEF, WITS, ODC, Google Drive)
- Stockage dual: Supabase (SQL) + ChromaDB (Vector DB)
- Analyses quotidiennes Perplexity (2 commodities: cashew, rubber)
- Génération de rapports Claude (mode MOCK template-based)
- Scheduler configuré pour exécution quotidienne à 6h00 Cambodia Time

⚠️ **État de Test**:
- **JAMAIS testé complètement en production**
- Mode MOCK fonctionnel et prêt
- Scripts de test créés mais non exécutés (dépendances manquantes)
- ChromaDB optionnel (fallback sur embedded mode)

💰 **Coûts Actuels**:
- Perplexity: $0.002 par exécution → **$0.06/mois**
- Claude: **$0** (MOCK mode)
- Total: **~$0.06/mois** (négligeable)

## Recommandations Immédiates (Semaine 1)

### 1. Installation et Configuration

**Priorité**: 🔴 CRITIQUE

```bash
# Installer les dépendances
pip install -r requirements.txt

# Vérifier la configuration
python scripts/test_daily_pipeline.py --dry-run
```

**Livrable**: Services tous opérationnels (Supabase, ChromaDB, Perplexity)

**Temps estimé**: 30 minutes

### 2. Premier Test MOCK Complet

**Priorité**: 🔴 CRITIQUE

```bash
# Test en mode MOCK (pas de coût)
python scripts/test_daily_pipeline.py
```

**Vérifications**:
- [ ] Pipeline se termine sans erreur
- [ ] 2 analyses Perplexity créées (cashew + rubber)
- [ ] 2 rapports Claude créés (cashew + rubber)
- [ ] Données visibles dans Supabase
- [ ] Embeddings dans ChromaDB (si serveur actif)

**Livrable**: Logs de test réussi + JSON de résultats

**Temps estimé**: 1 heure (incluant débugging si nécessaire)

### 3. Validation des Données

**Priorité**: 🟡 HAUTE

**Requêtes SQL à exécuter**:

```sql
-- Vérifier les analyses générées
SELECT
    c.name,
    COUNT(*) as total_analyses,
    MAX(pa.created_at) as last_analysis
FROM perplexity_analyses pa
JOIN commodities c ON c.id = pa.commodity_id
GROUP BY c.name;

-- Vérifier les rapports
SELECT
    c.name,
    COUNT(*) as total_reports,
    MAX(cr.created_at) as last_report
FROM claude_reports cr
JOIN commodities c ON c.id = cr.commodity_id
GROUP BY c.name;

-- Vérifier la qualité des données
SELECT
    c.name,
    COUNT(DISTINCT DATE(p.date)) as days_with_data,
    MIN(p.date) as first_date,
    MAX(p.date) as last_date,
    AVG(p.price_usd_per_unit) as avg_price
FROM prices p
JOIN commodities c ON c.id = p.commodity_id
GROUP BY c.name;
```

**Livrable**: Rapport de qualité des données

**Temps estimé**: 30 minutes

## Recommandations Court Terme (Mois 1)

### 4. ChromaDB Production Setup

**Priorité**: 🟡 HAUTE

**Contexte**: Actuellement ChromaDB peut fonctionner en mode embedded (fallback), mais un serveur dédié est recommandé pour production.

**Options**:

**Option A - Local Server** (développement/staging):
```bash
# Démarrer serveur local
chroma run --host localhost --port 8000 --path ./chroma_data

# Ou avec Docker
docker run -p 8000:8000 -v ./chroma_data:/chroma/chroma chromadb/chroma
```

**Option B - Cloud Hosted** (production):
- Chroma Cloud (service officiel)
- Self-hosted sur VPS (Digital Ocean, AWS EC2)
- Docker container dans infrastructure existante

**Recommandation**:
- Développement: Local server
- Production: Docker container self-hosted

**Coût estimé**:
- Local: $0
- VPS basic: $5-10/mois

**Livrable**: ChromaDB accessible 24/7

**Temps estimé**: 2-4 heures

### 5. Monitoring et Alertes

**Priorité**: 🟡 HAUTE

**Composants à monitorer**:

1. **Exécution quotidienne**:
   - Pipeline s'exécute chaque jour à 6h00
   - Durée d'exécution < 5 minutes
   - Aucune erreur critique

2. **Qualité des données**:
   - 2 analyses générées par jour
   - 2 rapports générés par jour
   - Pas de doublons

3. **Services externes**:
   - Supabase disponible
   - ChromaDB disponible
   - Perplexity API quota suffisant

**Solution Simple** (Python script):

```python
# scripts/daily_health_check.py
import asyncio
from datetime import date, datetime, timedelta
from app.services import SupabaseService
from app.config import settings

async def check_pipeline_health():
    """Vérifie que le pipeline a tourné aujourd'hui."""
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

    today = date.today()
    yesterday = today - timedelta(days=1)

    # Compter analyses créées aujourd'hui
    # Note: Nécessite une requête SQL custom
    # Pour l'instant, utiliser get_recent_analyses

    cashew = await supabase.get_or_create_commodity("cashew", "nut")
    analyses = await supabase.get_recent_analyses(cashew["id"], limit=10)

    recent_analyses = [a for a in analyses if a["created_at"].startswith(today.isoformat())]

    if len(recent_analyses) == 0:
        print(f"❌ ALERTE: Aucune analyse générée aujourd'hui ({today})")
        # Envoyer email/SMS
        return False
    else:
        print(f"✅ OK: {len(recent_analyses)} analyses générées aujourd'hui")
        return True

# Exécuter via cron chaque soir à 20h00
# 0 20 * * * cd /path/to/cambodia && python scripts/daily_health_check.py
```

**Solution Avancée** (recommandée):
- Uptime monitoring: Uptime Robot (gratuit)
- Application monitoring: Sentry (gratuit jusqu'à 5k events/mois)
- Logs centralisés: Logstash ou Better Stack

**Livrable**: Système d'alerte opérationnel

**Temps estimé**: 4-8 heures

### 6. Optimisation des Coûts Perplexity

**Priorité**: 🟢 MOYENNE

**Problème**: Chaque exécution quotidienne fait 2 appels Perplexity (cashew + rubber), soit 60 appels/mois.

**Solutions**:

**A. Caching intelligent** (recommandé):
```python
async def research_daily_prices_cached(commodity: str):
    """Utilise le cache si analyse récente existe."""
    # Vérifier si analyse < 24h existe
    recent = await supabase.get_recent_analyses(
        commodity_id,
        query_type="price",
        limit=1
    )

    if recent and is_within_24_hours(recent[0]["created_at"]):
        logger.info(f"Using cached Perplexity analysis for {commodity}")
        return recent[0]

    # Sinon, nouvelle requête
    return await perplexity.research_daily_prices(commodity)
```

**B. Fréquence réduite**:
- Analyse quotidienne → 3x par semaine
- Économie: 40% (~$0.04/mois → négligeable)

**C. Analyse conditionnelle**:
- Lancer Perplexity seulement si changement de prix > 5%
- Économie: 50-70% selon volatilité

**Recommandation**: Implémenter le caching (option A) - facile et efficace

**Gain**: Réduction 30-50% des coûts Perplexity

**Temps estimé**: 2 heures

## Recommandations Moyen Terme (Mois 2-3)

### 7. Migration Claude MOCK → REAL API

**Priorité**: 🟢 MOYENNE (selon budget disponible)

**Analyse coût/bénéfice**:

| Aspect | MOCK (actuel) | REAL (Claude API) |
|--------|--------------|------------------|
| Coût mensuel | $0 | ~$0.45 ($0.015 × 30 jours) |
| Qualité insights | Générique | Personnalisé, contextuel |
| Recommandations | Templates fixes | Basées sur données réelles |
| Citations | Aucune | Sources Perplexity intégrées |
| Personnalisation | Limitée | Illimitée |

**ROI estimé**:
- Coût additionnel: **$0.45/mois** (~$5.40/an)
- Bénéfice: Insights 3-5x plus actionnables
- **Recommandation**: Migrer si budget > $10/mois disponible

**Plan de migration**:

1. **Semaine 1**: Obtenir Claude API key
2. **Semaine 2**: Créer `ClaudeRealService` (copie de Mock avec API calls)
3. **Semaine 3**: Tests A/B (50% MOCK, 50% REAL)
4. **Semaine 4**: Migration complète si résultats satisfaisants

**Prompts recommandés pour Claude**:

```python
DAILY_REPORT_PROMPT = """
You are an agricultural commodities analyst specializing in Southeast Asian markets.

CONTEXT:
- Commodity: {commodity}
- Current price: ${price_usd}/ton ({change_pct}% vs yesterday)
- Volume traded: {volume_tons} tons
- Top destination: {destination}

PERPLEXITY ANALYSIS:
{perplexity_response}

TASK:
Generate a concise daily market report (300-400 words) with:

1. EXECUTIVE SUMMARY (2-3 sentences)
   - Price movement and significance
   - Key market driver today

2. INSIGHTS (3-5 bullet points)
   - What's driving the price?
   - Supply/demand dynamics
   - Geopolitical factors
   - Quality/seasonality impact

3. RECOMMENDATIONS (2-3 actionable items)
   - Timing for exports (hold vs. sell)
   - Risk mitigation strategies
   - Opportunities to explore

Style: Professional, data-driven, actionable
Audience: Agricultural exporters and policy makers
"""
```

**Temps estimé**: 8-12 heures

### 8. Dashboard Temps Réel

**Priorité**: 🟢 MOYENNE

**Objectif**: Visualiser l'exécution du pipeline et les résultats en temps réel.

**Technologies**:
- Streamlit (déjà dans le projet)
- Plotly pour graphiques
- Connexion Supabase en lecture seule

**Pages du dashboard**:

1. **Pipeline Health**:
   - Status de la dernière exécution
   - Durée d'exécution (graphique tendance)
   - Services status (Supabase, ChromaDB, APIs)

2. **Data Overview**:
   - Nombre de records par source
   - Couverture temporelle
   - Qualité des données (missing values, outliers)

3. **Price Trends**:
   - Graphiques prix cashew/rubber (30 jours)
   - Volumes exportés
   - Destinations principales

4. **Reports Library**:
   - Liste des rapports générés
   - Recherche par date/commodity
   - Téléchargement PDF

**Exemple code Streamlit**:

```python
# streamlit_app/pages/pipeline_health.py
import streamlit as st
from app.services import SupabaseService
from app.config import settings

st.title("🌅 Daily Pipeline Health")

supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

# Get stats
stats = await supabase.get_database_stats()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Analyses Today", stats["perplexity_analyses"])
with col2:
    st.metric("Reports Today", stats["claude_reports"])
with col3:
    st.metric("Prices Collected", stats["prices"])

# Last execution
st.subheader("Last Pipeline Execution")
# Parse latest log file
# Show status, duration, errors
```

**Livrable**: Dashboard accessible via `streamlit run streamlit_app/main.py`

**Temps estimé**: 16-24 heures

### 9. Notifications Email Automatiques

**Priorité**: 🟢 MOYENNE

**Objectif**: Envoyer rapports quotidiens par email aux stakeholders.

**Workflow**:
1. Pipeline s'exécute à 6h00
2. Rapports générés et stockés
3. Email envoyé à 7h00 avec:
   - Résumé exécutif (text)
   - Graphiques prix (embedded images)
   - Lien vers rapport complet (PDF)

**Technologies**:
- SendGrid (100 emails/jour gratuit)
- ou AWS SES ($0.10 per 1000 emails)
- ou SMTP simple (Gmail, Outlook)

**Code exemple**:

```python
# app/services/email_service.py
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

async def send_daily_report(
    recipient: str,
    cashew_report: dict,
    rubber_report: dict
):
    """Envoie le rapport quotidien par email."""

    sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)

    subject = f"Cambodia Agri Analytics - Daily Report {date.today()}"

    html_content = f"""
    <h2>Daily Market Report - {date.today()}</h2>

    <h3>Cashew</h3>
    <p>{cashew_report['insights'][0]}</p>
    <p><strong>Price:</strong> ${cashew_report['metadata']['price_usd']}/ton
       ({cashew_report['metadata']['price_change_pct']:+.2f}%)</p>

    <h3>Rubber</h3>
    <p>{rubber_report['insights'][0]}</p>
    <p><strong>Price:</strong> ${rubber_report['metadata']['price_usd']}/ton
       ({rubber_report['metadata']['price_change_pct']:+.2f}%)</p>

    <p><a href="https://your-dashboard.com/reports">View Full Reports</a></p>
    """

    message = Mail(
        from_email=Email("noreply@cambodia-agri.com"),
        to_emails=To(recipient),
        subject=subject,
        html_content=Content("text/html", html_content)
    )

    response = sg.client.mail.send.post(request_body=message.get())
    logger.info(f"Email sent to {recipient}: {response.status_code}")
```

**Intégration dans daily_pipeline**:

```python
# À la fin de daily_pipeline()
if settings.email_notifications_enabled:
    await send_daily_report(
        recipient=settings.stakeholder_email,
        cashew_report=cashew_report,
        rubber_report=rubber_report
    )
```

**Coût**: $0 (SendGrid free tier)

**Temps estimé**: 4-6 heures

## Recommandations Long Terme (Mois 4-6)

### 10. Machine Learning Predictions

**Priorité**: 🔵 BASSE (nice to have)

**Objectif**: Prédire les prix futurs basés sur données historiques.

**Modèles possibles**:
- ARIMA pour séries temporelles
- Prophet (Facebook) pour saisonnalité
- LSTM pour patterns complexes

**Intégration**:
```python
# Dans daily_pipeline, ajouter:
price_prediction = await ml_service.predict_next_week_prices("cashew")

# Inclure dans rapport Claude
cashew_report["predictions"] = {
    "next_week_price_usd": price_prediction["mean"],
    "confidence_interval": [price_prediction["lower"], price_prediction["upper"]],
    "model": "Prophet",
    "accuracy_last_month": "92%"
}
```

**Temps estimé**: 40-60 heures (recherche + implémentation + validation)

### 11. API Publique

**Priorité**: 🔵 BASSE

**Objectif**: Exposer les données et analyses via API REST.

**Endpoints**:
```
GET /api/v1/commodities
GET /api/v1/commodities/{id}/prices
GET /api/v1/commodities/{id}/latest-report
GET /api/v1/analyses?commodity=cashew&date=2025-01-15
POST /api/v1/search (semantic search ChromaDB)
```

**Technologies**: FastAPI (déjà dans le projet)

**Sécurité**: API keys, rate limiting

**Temps estimé**: 24-32 heures

### 12. Multi-commodity Expansion

**Priorité**: 🔵 BASSE

**Commodities à ajouter**:
- Rice (riz)
- Pepper (poivre de Kampot)
- Cassava (manioc)
- Bananas

**Changements requis**:
- Configuration: Liste commodities dynamique
- Collectors: Adapter pour nouveaux produits
- Perplexity: Nouveaux prompts spécialisés
- Storage: Aucun changement (générique)

**Temps estimé**: 12-16 heures par commodity

## Priorités Résumées

### Must Have (Semaine 1)
1. ✅ Installation dépendances
2. ✅ Premier test MOCK réussi
3. ✅ Validation données Supabase

### Should Have (Mois 1)
4. 🔄 ChromaDB production setup
5. 🔄 Monitoring et alertes
6. 🔄 Optimisation coûts Perplexity

### Nice to Have (Mois 2-3)
7. 💡 Migration Claude REAL
8. 💡 Dashboard temps réel
9. 💡 Email notifications

### Future (Mois 4+)
10. 🔮 ML predictions
11. 🔮 API publique
12. 🔮 Multi-commodity expansion

## Budget Estimé

### Coûts Actuels (MOCK mode)
- Perplexity: **$0.06/mois**
- Supabase: **$0** (free tier)
- ChromaDB: **$0** (self-hosted)
- **Total: $0.06/mois**

### Coûts avec Améliorations Court Terme
- Perplexity: $0.04/mois (avec caching)
- Claude API: $0.45/mois
- ChromaDB VPS: $5/mois
- Monitoring (Sentry): $0 (free tier)
- SendGrid: $0 (free tier)
- **Total: ~$5.50/mois**

### Coûts Production Complète
- APIs: ~$1/mois
- Infrastructure: ~$10/mois (VPS + backups)
- Services: $0-5/mois
- **Total: ~$15/mois**

## Conclusion

Le daily pipeline est **prêt à être testé et déployé** avec un coût négligeable en mode MOCK.

**Prochaines actions recommandées**:
1. ✅ Exécuter `pip install -r requirements.txt`
2. ✅ Lancer `python scripts/test_daily_pipeline.py --dry-run`
3. ✅ Lancer `python scripts/test_daily_pipeline.py` (test MOCK complet)
4. ✅ Valider les résultats dans Supabase
5. ✅ Activer le scheduler pour exécution quotidienne

Le système est conçu pour être **low-cost**, **scalable** et **facile à maintenir**.

Investissement temps total pour mise en production: **~40 heures** réparties sur 1 mois.
