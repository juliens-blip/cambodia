# 🚂 Railway - Configuration Minimaliste (RAPIDE)

## ⚡ Problème Résolu

Le build prenait **14+ minutes** et timeout car il installait:
- ❌ PyTorch (~2 GB)
- ❌ sentence-transformers (~1 GB)
- ❌ CUDA packages (~3 GB)
- ❌ Total: **~6-7 GB de dépendances**

## ✅ Solution: Build Minimal (2-3 minutes)

Utilisez `requirements-minimal.txt` qui installe **UNIQUEMENT** les dépendances essentielles (~150 MB).

---

## 📋 Configuration Railway (IMPORTANT)

### Étape 1: Configurer le Build Command

Dans Railway Dashboard:

1. Sélectionnez votre projet
2. **Settings** → **Build**
3. **Build Command**:
   ```bash
   pip install -r requirements-minimal.txt
   ```

### Étape 2: Configurer le Start Command

Dans **Settings** → **Deploy**:

**Start Command**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Étape 3: Redéployer

1. **Deployments** → **Redeploy**
2. Le build devrait prendre **2-3 minutes** au lieu de 14+

---

## 🎯 Fonctionnalités Disponibles

### ✅ Disponibles (Version Minimale)

- ✅ `/api/prices` - Prix export cashew/rubber
- ✅ `/api/production` - Données production
- ✅ `/api/reports` - Rapports générés
- ✅ `/api/search` - Recherche basique
- ✅ `/docs` - Documentation Swagger
- ✅ Collection données MEF/WITS/ODC
- ✅ Scheduler APScheduler (cron jobs)

### ❌ Non Disponibles (Nécessitent version complète)

- ❌ `/semantic` - Recherche sémantique (sentence-transformers)
- ❌ `/trends` - Analyse tendances ML
- ❌ ChromaDB - Stockage vectoriel
- ❌ PDF OCR - Processing documents
- ❌ Streamlit Dashboard

---

## 💾 Taille Comparée

| Version | Taille | Temps Build | Coût RAM |
|---------|--------|-------------|----------|
| **Complète** | ~6-7 GB | 14+ min (timeout) | 2-4 GB |
| **Minimale** | ~150 MB | 2-3 min | 512 MB |

---

## 🔄 Activer la Version Complète (Plus Tard)

Si vous voulez activer les features sémantiques:

### Option A: Utiliser un Service Dédié pour ML

1. Déployer l'API minimale sur Railway (rapide)
2. Déployer les features ML sur **Replicate** ou **Hugging Face Spaces**
3. Appeler via API

### Option B: Utiliser Railway avec Build Command Complet

```bash
# Dans Railway Settings → Build Command:
pip install -r requirements.txt
```

⚠️ **ATTENTION**: Build prendra 15-20 minutes et coûtera plus cher en RAM (~2-4 GB).

---

## 📊 Vérification du Déploiement

Une fois déployé, vérifiez:

1. **Logs** - Devrait afficher:
   ```
   ✅ Installing dependencies (2-3 min)
   ⚠️ Semantic/Trends routes not available
   ✅ Supabase initialized
   ✅ API startup complete
   ✅ Uvicorn running on port XXXX
   ```

2. **Health Check**:
   ```
   https://VOTRE_URL.up.railway.app/health
   ```

3. **API Docs**:
   ```
   https://VOTRE_URL.up.railway.app/docs
   ```

4. **Test Endpoint**:
   ```
   https://VOTRE_URL.up.railway.app/api/prices
   ```

---

## 🎯 Recommandation

**Pour production**: Utilisez la version **minimale** sur Railway.

Si vous avez besoin des features ML (semantic search):
- Déployez-les séparément sur **Replicate** (spécialisé ML)
- Ou utilisez **Google Cloud Run** (meilleur support ML que Railway)

---

## 📞 Support

Si le build timeout encore:
1. Vérifiez que Build Command = `pip install -r requirements-minimal.txt`
2. Redémarrez le build
3. Vérifiez les logs pour voir quelle dépendance prend du temps

**Build minimal devrait réussir en 2-3 minutes!** 🚀
