# Documentation Index - Cambodia Agri Analytics

Guide rapide pour trouver la documentation appropriée selon votre besoin.

## Je veux...

### 🚀 Tester le Pipeline Rapidement (10 min)

→ **Lire**: `QUICK_START_TESTING.md`

**Vous allez apprendre**:
- Installation en 2 minutes
- Commande de test simple
- Vérification des résultats
- Troubleshooting rapide

**Commande clé**:
```bash
python scripts/test_daily_pipeline.py
```

---

### 📚 Comprendre l'Architecture du Pipeline

→ **Lire**: `docs/DAILY_PIPELINE_GUIDE.md`

**Vous allez apprendre**:
- Comment fonctionne le daily_pipeline
- Flux de données détaillé (4 phases)
- Tables Supabase affectées
- Collections ChromaDB
- Modes MOCK vs REAL
- Gestion des erreurs
- Optimisations possibles

**Idéal pour**: Développeurs, architectes, tech leads

---

### 🧪 Faire des Tests Complets

→ **Lire**: `docs/TESTING_GUIDE.md`

**Vous allez apprendre**:
- 4 modes de test (dry-run, MOCK, REAL, skip-collectors)
- Interpréter les résultats (logs, JSON)
- Vérifier Supabase et ChromaDB
- Erreurs communes et solutions
- Best practices de test
- Performance benchmarks

**Idéal pour**: QA, testeurs, développeurs

---

### 📋 Voir les Recommandations et Roadmap

→ **Lire**: `docs/PIPELINE_RECOMMENDATIONS.md`

**Vous allez apprendre**:
- Recommandations court/moyen/long terme
- Priorités (must have, should have, nice to have)
- Budgets détaillés (actuel: $0.06/mois)
- ROI analysis pour chaque feature
- Code examples pour optimisations
- Timeline estimée

**Idéal pour**: Product managers, décideurs, planification

---

### 🛠️ Développer de Nouveaux Scripts

→ **Lire**: `scripts/README.md`

**Vous allez apprendre**:
- Scripts disponibles et leur usage
- Template de base pour nouveaux scripts
- Best practices développement
- Configuration cron/automation
- Troubleshooting scripts

**Idéal pour**: Développeurs backend

---

### 📊 Voir le Résumé Complet du Projet

→ **Lire**: `DAILY_PIPELINE_TEST_DELIVERABLES.md`

**Vous allez apprendre**:
- Résumé exécutif
- Tous les livrables créés
- État actuel du pipeline
- Configuration validée
- Métriques de succès
- Risques et mitigations
- Timeline et coûts

**Idéal pour**: Stakeholders, management, audit

---

### 🏗️ Comprendre l'Architecture Globale

→ **Lire**: `RESUME_CODEX.md`

**Vous allez apprendre**:
- Architecture complète du projet
- 7 tables Supabase
- 5 collections ChromaDB
- 4 collectors de données
- Services et APIs
- État actuel de chaque composant

**Idéal pour**: Onboarding, vision d'ensemble

---

## Par Rôle

### Développeur Backend

**Lecture recommandée** (ordre):
1. `QUICK_START_TESTING.md` - Premier test rapide
2. `docs/DAILY_PIPELINE_GUIDE.md` - Architecture technique
3. `docs/TESTING_GUIDE.md` - Tests approfondis
4. `scripts/README.md` - Développement scripts

**Temps**: ~2 heures de lecture

---

### QA / Testeur

**Lecture recommandée** (ordre):
1. `QUICK_START_TESTING.md` - Setup test
2. `docs/TESTING_GUIDE.md` - Guide de test complet
3. `docs/DAILY_PIPELINE_GUIDE.md` - Comprendre ce qui est testé

**Temps**: ~1 heure de lecture

---

### Product Manager / Tech Lead

**Lecture recommandée** (ordre):
1. `DAILY_PIPELINE_TEST_DELIVERABLES.md` - État et livrables
2. `docs/PIPELINE_RECOMMENDATIONS.md` - Roadmap et budgets
3. `docs/DAILY_PIPELINE_GUIDE.md` - Détails techniques

**Temps**: ~1.5 heures de lecture

---

### Stakeholder / Management

**Lecture recommandée**:
1. `DAILY_PIPELINE_TEST_DELIVERABLES.md` - Section "Résumé Exécutif"
2. `docs/PIPELINE_RECOMMENDATIONS.md` - Section "Budgets" et "ROI"

**Temps**: ~20 minutes de lecture

---

## Par Tâche

### Tâche: Premier Test du Pipeline

**Documents nécessaires**:
1. `QUICK_START_TESTING.md` - Workflow complet
2. `docs/TESTING_GUIDE.md` - Référence si problème

**Fichiers à exécuter**:
- `scripts/test_daily_pipeline.py --dry-run`
- `scripts/test_daily_pipeline.py`

**Durée**: 15 minutes

---

### Tâche: Déployer en Production

**Documents nécessaires**:
1. `docs/TESTING_GUIDE.md` - Tests de validation
2. `docs/PIPELINE_RECOMMENDATIONS.md` - Section "Court Terme"
3. `docs/DAILY_PIPELINE_GUIDE.md` - Section "Configuration"

**Checklist**:
- [ ] Tests MOCK passent
- [ ] UN test REAL réussi
- [ ] ChromaDB configuré
- [ ] Monitoring setup
- [ ] Scheduler activé

**Durée**: 1-2 jours

---

### Tâche: Debugger une Erreur

**Documents nécessaires**:
1. `docs/TESTING_GUIDE.md` - Section "Erreurs Communes"
2. `docs/DAILY_PIPELINE_GUIDE.md` - Section "Troubleshooting"
3. `scripts/README.md` - Troubleshooting scripts

**Fichiers logs à vérifier**:
- `logs/test_daily_pipeline_*.log`
- `logs/pipeline_test_results_*.json`

---

### Tâche: Optimiser les Coûts

**Documents nécessaires**:
1. `docs/PIPELINE_RECOMMENDATIONS.md` - Section "Optimisation Coûts Perplexity"
2. `docs/DAILY_PIPELINE_GUIDE.md` - Section "Optimisations Possibles"

**Code à modifier**:
- `app/services/perplexity_service.py` - Ajouter caching
- `app/scheduler/jobs.py` - Analyse conditionnelle

---

### Tâche: Migrer vers Claude REAL

**Documents nécessaires**:
1. `docs/PIPELINE_RECOMMENDATIONS.md` - Section "Migration Claude MOCK → REAL"
2. `docs/DAILY_PIPELINE_GUIDE.md` - Section "Modes de Fonctionnement"

**Fichiers à modifier**:
- `.env` - `CLAUDE_MOCK_MODE=false`
- Créer `app/services/claude_real_service.py`
- Modifier `app/scheduler/jobs.py` - Importer nouveau service

**Durée**: 8-12 heures

---

### Tâche: Créer un Dashboard

**Documents nécessaires**:
1. `docs/PIPELINE_RECOMMENDATIONS.md` - Section "Dashboard Temps Réel"
2. `RESUME_CODEX.md` - Architecture Supabase

**Technologies**:
- Streamlit (déjà dans projet)
- Plotly pour graphiques
- Connexion Supabase lecture seule

**Durée**: 16-24 heures

---

## Structure des Documents

```
D:\Projects\cambodia\
│
├── QUICK_START_TESTING.md              [Guide 10 min]
├── DAILY_PIPELINE_TEST_DELIVERABLES.md [Résumé complet]
├── RESUME_CODEX.md                     [Architecture globale]
│
├── docs/
│   ├── INDEX.md                        [Ce fichier]
│   ├── DAILY_PIPELINE_GUIDE.md         [Technique détaillé]
│   ├── TESTING_GUIDE.md                [Guide tests]
│   └── PIPELINE_RECOMMENDATIONS.md     [Roadmap & budgets]
│
├── scripts/
│   ├── README.md                       [Documentation scripts]
│   ├── test_daily_pipeline.py          [Script test principal]
│   └── seed.py                         [Seeding base]
│
└── logs/
    ├── test_daily_pipeline_*.log       [Logs détaillés]
    └── pipeline_test_results_*.json    [Résultats JSON]
```

## Taille des Documents

| Document | Taille | Temps Lecture |
|----------|--------|---------------|
| `QUICK_START_TESTING.md` | ~1500 mots | 5-10 min |
| `DAILY_PIPELINE_GUIDE.md` | ~4000 mots | 20-30 min |
| `TESTING_GUIDE.md` | ~3000 mots | 15-20 min |
| `PIPELINE_RECOMMENDATIONS.md` | ~5000 mots | 25-35 min |
| `DAILY_PIPELINE_TEST_DELIVERABLES.md` | ~4000 mots | 20-30 min |
| `scripts/README.md` | ~2000 mots | 10-15 min |
| `INDEX.md` | ~1000 mots | 5 min |

**Total documentation**: ~20000 mots (~90 minutes lecture complète)

## FAQ Rapide

### Q: Par où commencer?

**R**: `QUICK_START_TESTING.md` - 10 minutes pour tester le pipeline

### Q: Le pipeline a échoué, que faire?

**R**: `docs/TESTING_GUIDE.md` section "Erreurs Communes et Solutions"

### Q: Combien ça coûte de faire tourner le pipeline?

**R**: `docs/PIPELINE_RECOMMENDATIONS.md` section "Coûts Estimés"
- Actuellement: **$0.06/mois**
- Production: **$0.51-5.51/mois**

### Q: Comment activer le mode REAL pour Claude?

**R**: `docs/DAILY_PIPELINE_GUIDE.md` section "Modes de Fonctionnement"
- `.env`: `CLAUDE_MOCK_MODE=false`
- Ajouter `CLAUDE_API_KEY=sk-ant-...`

### Q: Le pipeline génère des doublons, comment les supprimer?

**R**: `docs/DAILY_PIPELINE_GUIDE.md` section "Troubleshooting - Doublons"
- SQL queries pour identifier
- SQL queries pour nettoyer

### Q: Comment créer un nouveau script utilitaire?

**R**: `scripts/README.md` section "Développement de Nouveaux Scripts"
- Template de base fourni
- Best practices incluses

### Q: Quelle est la roadmap pour les 6 prochains mois?

**R**: `docs/PIPELINE_RECOMMENDATIONS.md` sections priorités
- Semaine 1: Tests
- Mois 1: Production ready
- Mois 2-3: Features avancées
- Mois 4-6: ML, API publique

## Changelog Documentation

### Version 1.0 (2025-01-15)

**Créé**:
- ✅ Quick Start Guide
- ✅ Daily Pipeline Guide (technique)
- ✅ Testing Guide
- ✅ Recommendations & Roadmap
- ✅ Scripts README
- ✅ Deliverables Summary
- ✅ Index (ce fichier)

**Code**:
- ✅ `test_daily_pipeline.py` (script test complet)
- ✅ `requirements.txt` (dépendances)

**Total**: 7 documents + 2 fichiers code

---

**Navigation rapide**:
- 🏠 Retour au projet: `README.md`
- 📘 Architecture globale: `RESUME_CODEX.md`
- 🚀 Premier test: `QUICK_START_TESTING.md`
- 📊 État du projet: `DAILY_PIPELINE_TEST_DELIVERABLES.md`
