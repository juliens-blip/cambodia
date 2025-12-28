# Production Data Collection - Documentation Index

Documentation complète du système de collecte de données de production pour Cambodia Agri Analytics.

## Documents Disponibles

### 📚 Guides Utilisateur

#### [QUICKSTART_PRODUCTION.md](../QUICKSTART_PRODUCTION.md)
**Pour:** Démarrage rapide
**Contenu:**
- 5 étapes simples pour activer production data
- Commandes PowerShell copy-paste ready
- Troubleshooting rapide
- Vérification SQL

**Quand l'utiliser:** Premier setup ou référence rapide

---

#### [PRODUCTION_DATA_SETUP.md](../PRODUCTION_DATA_SETUP.md)
**Pour:** Guide complet de setup
**Contenu:**
- Vue d'ensemble architecture
- Installation & configuration détaillée
- Utilisation (test, seed, vérification)
- Structure des données
- Extraction methods (PDF, KML)
- Troubleshooting approfondi
- Workflow complet
- Dashboard visualization

**Quand l'utiliser:** Setup initial complet ou référence détaillée

---

### 🏗️ Documentation Technique

#### [ARCHITECTURE_PRODUCTION.md](../ARCHITECTURE_PRODUCTION.md)
**Pour:** Développeurs et architecture
**Contenu:**
- Diagramme architecture complète
- Components détaillés (collectors, parsers, storage)
- Data flow avec exemples concrets
- Database schema
- Error handling
- Performance considerations
- Testing
- Configuration
- Deployment

**Quand l'utiliser:** Développement, debugging, architecture review

---

#### [scripts/migrations/README.md](../scripts/migrations/README.md)
**Pour:** Migrations base de données
**Contenu:**
- How to apply migrations
- Migration 001: Prices unique constraint
- Migration 002: Production unique constraint
- Natural key definitions
- Rollback procedures
- Migration status tracking

**Quand l'utiliser:** Avant seeding, database setup

---

### 📝 Documentation Projet

#### [RESUME_CODEX.md](../RESUME_CODEX.md)
**Pour:** Contexte global projet (handoff Codex → Claude)
**Contenu:**
- Current status (API, Dashboard, Data)
- Data sources (MEF, WITS, GDrive, ODC)
- OCR/PDF parsing setup
- Storage behavior (Supabase, ChromaDB)
- Dashboard state
- Commands to run locally
- Known issues
- **Section 13:** Production data collection (fait par Claude)
- Recommended next steps

**Quand l'utiliser:** Onboarding, contexte général

---

#### [MEMOIRE_CLAUDE.md](../MEMOIRE_CLAUDE.md)
**Pour:** Logs détaillés sessions (Codex + Claude)
**Contenu:**
- Informations sensibles (API keys)
- Sources de données
- Objectif projet
- Sessions chronologiques avec tags "(fait par codex)" et "(fait par Claude)"
- **Dernière session:** Système production data (2025-12-25)

**Quand l'utiliser:** Historique détaillé, debugging problèmes passés

---

## Organisation par Use Case

### ✅ "Je veux juste activer production data"
1. [QUICKSTART_PRODUCTION.md](../QUICKSTART_PRODUCTION.md)
2. Apply migrations (copy-paste SQL)
3. Run: `python scripts/seed_collectors.py --include-odc`

### 🔧 "Je veux comprendre comment ça marche"
1. [PRODUCTION_DATA_SETUP.md](../PRODUCTION_DATA_SETUP.md) - Overview + setup
2. [ARCHITECTURE_PRODUCTION.md](../ARCHITECTURE_PRODUCTION.md) - Technical details

### 🐛 "J'ai un problème"
1. [QUICKSTART_PRODUCTION.md](../QUICKSTART_PRODUCTION.md) - Troubleshooting rapide
2. [PRODUCTION_DATA_SETUP.md](../PRODUCTION_DATA_SETUP.md) - Troubleshooting approfondi
3. [MEMOIRE_CLAUDE.md](../MEMOIRE_CLAUDE.md) - Historique problèmes connus

### 👨‍💻 "Je veux contribuer/développer"
1. [ARCHITECTURE_PRODUCTION.md](../ARCHITECTURE_PRODUCTION.md) - Architecture complète
2. [RESUME_CODEX.md](../RESUME_CODEX.md) - Contexte projet
3. Code source:
   - `app/collectors/odc_collector.py`
   - `app/collectors/gdrive_collector.py`
   - `app/utils/kml_parser.py`
   - `app/services/supabase_service.py`

### 🗄️ "Je veux gérer la base de données"
1. [scripts/migrations/README.md](../scripts/migrations/README.md) - Migrations
2. [ARCHITECTURE_PRODUCTION.md](../ARCHITECTURE_PRODUCTION.md) - Database schema
3. Migration files:
   - `scripts/migrations/001_add_unique_constraint_prices.sql`
   - `scripts/migrations/002_add_unique_constraint_production.sql`

## Arborescence Fichiers

```
D:\Projects\cambodia\
├── QUICKSTART_PRODUCTION.md          # ⚡ Quick start
├── PRODUCTION_DATA_SETUP.md          # 📘 Setup complet
├── ARCHITECTURE_PRODUCTION.md        # 🏗️ Architecture
├── RESUME_CODEX.md                   # 📝 Contexte projet
├── MEMOIRE_CLAUDE.md                 # 📋 Logs sessions
│
├── app/
│   ├── collectors/
│   │   ├── odc_collector.py          # ODC scraping
│   │   └── gdrive_collector.py       # PDF/KML extraction
│   ├── services/
│   │   └── supabase_service.py       # upsert_production()
│   └── utils/
│       └── kml_parser.py             # KML parsing utility
│
├── scripts/
│   ├── test_production_seeding.py    # Test script
│   ├── seed_collectors.py            # Seed script
│   └── migrations/
│       ├── README.md                 # 🗄️ Migrations doc
│       ├── 001_...prices.sql
│       └── 002_...production.sql
│
└── docs/
    └── README_PRODUCTION.md          # 📚 Ce fichier
```

## Flux de Lecture Recommandé

### Pour débutant
```
QUICKSTART_PRODUCTION.md
    ↓
Appliquer migrations
    ↓
Run seed
    ↓
PRODUCTION_DATA_SETUP.md (troubleshooting si besoin)
```

### Pour utilisateur avancé
```
PRODUCTION_DATA_SETUP.md (overview)
    ↓
ARCHITECTURE_PRODUCTION.md (comprendre)
    ↓
Code source (explorer)
    ↓
Test & seed
```

### Pour développeur
```
RESUME_CODEX.md (contexte global)
    ↓
ARCHITECTURE_PRODUCTION.md (architecture)
    ↓
Code source (app/collectors/, app/utils/)
    ↓
MEMOIRE_CLAUDE.md (historique)
```

## Checklist Production Data

### Setup Initial
- [ ] Lire QUICKSTART_PRODUCTION.md
- [ ] Appliquer migration 001 (prices)
- [ ] Appliquer migration 002 (production)
- [ ] Vérifier .env (TESSERACT_CMD, POPPLER_PATH, etc.)
- [ ] Run test: `python scripts/test_production_seeding.py`
- [ ] Seed: `python scripts/seed_collectors.py --include-odc`
- [ ] Vérifier Supabase: `SELECT COUNT(*) FROM production;`
- [ ] Dashboard > Production Maps

### Maintenance
- [ ] Re-seed safe (upsert, no duplicates)
- [ ] Monitor logs (INFO/WARNING/ERROR)
- [ ] Check stats: `GET /stats`
- [ ] Daily pipeline runs automatically (6:00 AM Cambodia Time)

## Support & Contact

### Documentation
1. Vérifier QUICKSTART (troubleshooting rapide)
2. Vérifier PRODUCTION_DATA_SETUP (troubleshooting approfondi)
3. Vérifier ARCHITECTURE (technical deep dive)

### Logs
```powershell
# Run seed avec logs
.\.venv311\Scripts\python.exe scripts\seed_collectors.py --include-odc

# Run test avec logs
.\.venv311\Scripts\python.exe scripts\test_production_seeding.py
```

### Database
```sql
-- Check production table
SELECT * FROM production LIMIT 10;

-- Check duplicates (should be 0)
SELECT commodity_id, year, province, source, COUNT(*)
FROM production
GROUP BY commodity_id, year, province, source
HAVING COUNT(*) > 1;
```

---

## Versions

| Document | Version | Date | Status |
|----------|---------|------|--------|
| QUICKSTART_PRODUCTION.md | 1.0 | 2025-12-25 | ✅ Ready |
| PRODUCTION_DATA_SETUP.md | 1.0 | 2025-12-25 | ✅ Ready |
| ARCHITECTURE_PRODUCTION.md | 1.0 | 2025-12-25 | ✅ Ready |
| migrations/002_...production.sql | 1.0 | 2025-12-25 | ⏳ Apply |

---

**Maintainer:** Claude Code (session 2025-12-25)
**Project:** Cambodia Agri Analytics
**Status:** Production Ready
