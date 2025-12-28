# 🚀 START HERE - Quick Start Guide

**Status:** ✅ **TOUT EST PRÊT**
**Date:** 2025-12-27

---

## 🟢 Services Actifs

### 1. API Server
- **URL:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **Status:** 🟢 RUNNING

### 2. Streamlit UI
- **URL:** http://localhost:8501
- **Status:** 🟢 RUNNING

---

## 🎯 Comment Démarrer

### Option 1: Interface Web (Recommandé)

**Ouvrir dans votre navigateur:**
```
http://localhost:8501
```

**Pages disponibles:**
- 🔍 **Search** - Recherche sémantique (GRATUIT)
- 💬 **AI Q&A** - Questions intelligentes ($0.005)
- 📚 **History** - Historique conversations
- 📊 **Admin** - Dashboard & budget
- 📈 **Market Trends** - Analyses marché (NOUVEAU ⭐)

### Option 2: API REST

**Documentation interactive:**
```
http://localhost:8000/docs
```

**Exemples rapides:**
```bash
# Health check
curl http://localhost:8000/health

# Budget status
curl http://localhost:8000/api/v1/stats

# Market trends summary
curl http://localhost:8000/api/v1/trends/summary
```

---

## 📈 Résultats Actuels

### Cashew (Noix de Cajou)
- **Tendance:** ➡️ Neutral
- **Prix:** -5%
- **Sentiment:** 😐 Neutral

### Rubber (Caoutchouc)
- **Tendance:** 📈🔥 Strong Bullish
- **Prix:** +1.24% (~1,798 USD/tonne)
- **Sentiment:** 😊 Bullish

---

## 💰 Budget

- **Limite:** $5.00 / mois
- **Utilisé:** $0.01 (0.2%)
- **Restant:** $4.99 (99.8%)

**Coûts:**
- Recherche: $0 (gratuit)
- RAG Q&A: $0.005
- Market Trends (auto): $0.01/jour

---

## ⚙️ Automatisation Quotidienne

**Configurer Windows Task Scheduler:**

1. Ouvrir `taskschd.msc`
2. Créer tâche: "Cambodia Agri - Daily Market Trends"
3. Trigger: Tous les jours à 9h00
4. Action:
   - Programme: `python`
   - Arguments: `scripts\daily_market_trends.py`
   - Démarrer dans: `D:\Projects\cambodia`

**Test manuel:**
```bash
python scripts/daily_market_trends.py
```

---

## 📚 Documentation Complète

**Guides:**
- `INSTALLATION_COMPLETE.md` - Guide complet (17 KB)
- `TEST_RESULTS.md` - Résultats tests
- `docs/MARKET_TRENDS.md` - Guide market trends (90 KB)

**Quick Links:**
- Admin: http://localhost:8501/Admin
- Market Trends: http://localhost:8501/Market_Trends
- API Docs: http://localhost:8000/docs

---

## 🎯 Prochaines Étapes

1. ✅ **Explorer l'Interface**
   - Tester toutes les pages Streamlit
   - Poser des questions RAG
   - Consulter les tendances

2. ⏳ **Configurer l'Automatisation**
   - Setup Task Scheduler
   - Vérifier exécution demain

3. ⏳ **Monitorer le Budget**
   - Consulter Admin dashboard
   - Observer les coûts

---

## 🆘 Besoin d'Aide ?

**Problème courant:**
- Services arrêtés ? Redémarrer:
  ```bash
  # Terminal 1
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

  # Terminal 2
  python -m streamlit run ui/streamlit_app.py
  ```

**Documentation:**
- Lire `INSTALLATION_COMPLETE.md` pour guide détaillé
- Lire `TEST_RESULTS.md` pour résultats tests
- Consulter http://localhost:8000/docs pour API

---

**Status:** ✅ **100% OPÉRATIONNEL**

🎉 **Profitez de votre système d'intelligence agricole !**
