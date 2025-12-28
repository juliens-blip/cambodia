# Scripts Directory - Cambodia Agri Analytics

Ce dossier contient les scripts utilitaires et de test pour le projet Cambodia Agri Analytics.

## Scripts Disponibles

### 1. test_daily_pipeline.py

**Description**: Script de test complet pour le daily_pipeline

**Usage**:
```bash
# Test avec services check seulement (pas d'exécution)
python scripts/test_daily_pipeline.py --dry-run

# Test complet en mode MOCK (pas de coûts API)
python scripts/test_daily_pipeline.py

# Test avec vraies API Perplexity (coûts: ~$0.002)
python scripts/test_daily_pipeline.py --real

# Test sans collectors (analyse uniquement)
python scripts/test_daily_pipeline.py --skip-collectors
```

**Output**:
- Logs détaillés: `logs/test_daily_pipeline_YYYYMMDD_HHMMSS.log`
- Résultats JSON: `logs/pipeline_test_results_YYYYMMDD_HHMMSS.json`

**Quand utiliser**:
- Avant déploiement
- Après modifications du pipeline
- Pour diagnostiquer problèmes
- Tests de régression

**Documentation**: Voir `docs/TESTING_GUIDE.md`

---

### 2. seed.py

**Description**: Script de seeding initial de la base de données

**Usage**:
```bash
python scripts/seed.py
```

**Ce qu'il fait**:
- Crée les commodities (cashew, rubber)
- Insert des données de test (prices, production)
- Initialise ChromaDB avec embeddings
- Configure data_sources table

**Quand utiliser**:
- Setup initial du projet
- Reset de la base de test
- Après migration Supabase

**Note**: Ne génère PAS d'analyses Perplexity (seulement le daily_pipeline le fait)

---

### Scripts Futurs (à créer)

#### daily_health_check.py

**Description**: Vérifie que le pipeline s'est exécuté correctement

**Usage prévu**:
```bash
python scripts/daily_health_check.py
```

**À implémenter**:
- Vérifie analyses/rapports générés aujourd'hui
- Alerte si problème détecté
- Envoie notification si nécessaire

**Exécution**: Via cron à 20h00 chaque soir

---

#### cleanup_duplicates.py

**Description**: Nettoie les doublons dans Supabase

**Usage prévu**:
```bash
python scripts/cleanup_duplicates.py --table perplexity_analyses --dry-run
python scripts/cleanup_duplicates.py --table perplexity_analyses --execute
```

**Cas d'usage**: Pipeline exécuté plusieurs fois par erreur

---

#### backup_chromadb.py

**Description**: Sauvegarde ChromaDB collections

**Usage prévu**:
```bash
python scripts/backup_chromadb.py --output backups/chromadb_20250115.tar.gz
```

**Exécution**: Hebdomadaire via cron

---

#### export_reports.py

**Description**: Exporte les rapports en PDF

**Usage prévu**:
```bash
# Export rapport du jour
python scripts/export_reports.py --date 2025-01-15 --format pdf

# Export semaine complète
python scripts/export_reports.py --week 2025-W02 --format pdf --output weekly_reports/
```

---

## Configuration Requise

### Variables d'Environnement

Tous les scripts utilisent les variables du fichier `.env`:

```bash
# Minimum requis
SUPABASE_URL=https://...
SUPABASE_KEY=eyJhbGci...
PERPLEXITY_API_KEY=pplx-...

# ChromaDB (optionnel)
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Claude (optionnel si MOCK mode)
CLAUDE_MOCK_MODE=true
```

### Dépendances

Installer avec:
```bash
pip install -r requirements.txt
```

Packages principaux:
- `supabase` - Connexion base de données
- `chromadb` - Vector database
- `httpx` - HTTP client async
- `apscheduler` - Scheduler

## Logs et Output

### Structure Logs

```
logs/
├── test_daily_pipeline_20250115_143022.log
├── test_daily_pipeline_20250115_143022.json
├── seed_20250114_120500.log
└── daily_health_check_20250115_200000.log
```

### Format Logs

```
2025-01-15 14:30:22 - app.scheduler.jobs - INFO - 🌅 Starting DAILY pipeline...
2025-01-15 14:30:23 - app.collectors.mef - INFO - Collecting data from MEF API...
2025-01-15 14:30:45 - app.services.supabase - INFO - Upserted price: cashew on 2025-01-15
2025-01-15 14:31:02 - app.services.perplexity - INFO - Perplexity query successful for cashew
2025-01-15 14:31:15 - app.scheduler.jobs - INFO - ✅ DAILY pipeline complete!
```

### JSON Results Schema

```json
{
  "test_started_at": "2025-01-15T14:30:22",
  "mock_mode": true,
  "service_status": {
    "supabase": true,
    "chromadb": true,
    "perplexity": true,
    "claude": true
  },
  "baseline": {
    "supabase": {
      "perplexity_analyses": 0,
      "claude_reports": 0,
      "prices": 1415
    }
  },
  "pipeline_execution": {
    "success": true,
    "duration_seconds": 142.5
  },
  "verification": {
    "supabase_changes": {
      "perplexity_analyses": 2,
      "claude_reports": 2
    },
    "all_checks_passed": true
  },
  "overall_success": true
}
```

## Développement de Nouveaux Scripts

### Template de Base

```python
"""
Script description here.

Usage:
    python scripts/my_script.py [options]
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings
from app.services import SupabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main script logic."""
    logger.info("Starting script...")

    # Your code here
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

    logger.info("Script completed")


if __name__ == "__main__":
    asyncio.run(main())
```

### Best Practices

1. **Toujours utiliser logging** (pas de print)
2. **Async/await** pour I/O operations
3. **Gestion d'erreurs** appropriée
4. **Dry-run mode** pour scripts dangereux
5. **Documenter usage** en docstring
6. **Arguments CLI** avec argparse

### Test d'un Nouveau Script

```bash
# 1. Créer le script
touch scripts/my_script.py

# 2. Rendre exécutable (Linux/Mac)
chmod +x scripts/my_script.py

# 3. Tester
python scripts/my_script.py --help
python scripts/my_script.py --dry-run
python scripts/my_script.py
```

## Troubleshooting

### Problème: ModuleNotFoundError

```
ModuleNotFoundError: No module named 'app'
```

**Solution**: Le script ajoute automatiquement le project root au path. Vérifier que:
```python
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

### Problème: Import ChromaDB Failed

```
ModuleNotFoundError: No module named 'chromadb'
```

**Solution**:
```bash
pip install -r requirements.txt
```

### Problème: Supabase Connection Failed

**Solution**: Vérifier `.env`:
```bash
cat .env | grep SUPABASE
```

### Problème: Permission Denied (Linux)

```bash
chmod +x scripts/my_script.py
```

## Automatisation avec Cron

### Linux/Mac

```bash
# Éditer crontab
crontab -e

# Daily pipeline à 6h00
0 6 * * * cd /path/to/cambodia && /path/to/python scripts/test_daily_pipeline.py

# Health check à 20h00
0 20 * * * cd /path/to/cambodia && /path/to/python scripts/daily_health_check.py

# Backup ChromaDB chaque dimanche à 3h00
0 3 * * 0 cd /path/to/cambodia && /path/to/python scripts/backup_chromadb.py
```

### Windows (Task Scheduler)

```powershell
# Créer tâche planifiée
schtasks /create /tn "CambodiaAgriDailyPipeline" /tr "python D:\Projects\cambodia\scripts\test_daily_pipeline.py" /sc daily /st 06:00
```

## Documentation

Pour plus de détails:

- **Architecture du pipeline**: `docs/DAILY_PIPELINE_GUIDE.md`
- **Guide de test**: `docs/TESTING_GUIDE.md`
- **Recommandations**: `docs/PIPELINE_RECOMMENDATIONS.md`
- **Codex général**: `RESUME_CODEX.md`
