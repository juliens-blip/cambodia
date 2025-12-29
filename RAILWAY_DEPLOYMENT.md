# 🚂 Railway Deployment - Solution Docker

## Le Problème

Les erreurs suivantes sont des problèmes **d'infrastructure Railway**, pas de ton code:

```
runc run failed: container process is already dead
CNI setup error: plugin type="loopback" failed (add): interrupted system call
```

Ces erreurs sont liées à nixpacks/mise qui sont parfois instables sur Railway. 
La solution est d'utiliser **Docker** directement.

---

## ✅ Solution: Utiliser Docker

J'ai créé les fichiers suivants pour un déploiement stable:

### Fichiers créés:

1. **`Dockerfile`** - Image Docker optimisée pour Railway
2. **`.dockerignore`** - Réduit la taille du build
3. **`railway.toml`** - Configuration Railway pour utiliser Docker

---

## 🚀 Instructions de Déploiement

### Étape 1: Push sur GitHub

```bash
git add Dockerfile .dockerignore railway.toml
git commit -m "chore: add Docker configuration for Railway"
git push
```

### Étape 2: Sur Railway Dashboard

1. Aller sur https://railway.app/dashboard
2. Sélectionner ton projet
3. Railway devrait détecter automatiquement le Dockerfile

### Étape 3: Configurer les Variables d'Environnement

Dans **Settings** → **Variables**:

```env
SUPABASE_URL=ta_url_supabase
SUPABASE_ANON_KEY=ta_cle_supabase
PERPLEXITY_API_KEY=ta_cle_perplexity
GOOGLE_DOCS_API_KEY=ta_cle_google (optionnel)
ENVIRONMENT=production
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
```

### Étape 4: Redéployer

Click sur **Redeploy** ou push un nouveau commit.

---

## 🔧 Si les erreurs persistent

Les erreurs `runc` et `CNI` sont **côté Railway**, pas ton code. Options:

### Option A: Réessayer
Railway a parfois des problèmes d'infrastructure temporaires. Attends quelques minutes et redéploie.

### Option B: Changer de région
Dans Railway Settings:
- Service Settings → Region → Choisir une autre région

### Option C: Contacter Railway Support
Si les erreurs persistent, c'est un problème d'infrastructure Railway.
- https://railway.app/support
- Discord: https://discord.gg/railway

### Option D: Alternative - Render.com
Render.com est une alternative gratuite et stable:
1. Aller sur https://render.com
2. Créer un nouveau "Web Service"
3. Connecter ton repo GitHub
4. Il détectera automatiquement le Dockerfile

---

## 📋 Fichiers de Configuration

### Dockerfile
```dockerfile
FROM python:3.11-slim-bookworm
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils
COPY requirements-railway.txt ./
RUN pip install --no-cache-dir -r requirements-railway.txt
COPY app/ ./app/
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### railway.toml
```toml
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/health"
restartPolicyType = "ON_FAILURE"
```

---

## ✅ Endpoints à Tester

Une fois déployé:
- **Health**: `https://ton-app.up.railway.app/health`
- **API Docs**: `https://ton-app.up.railway.app/docs`
- **Root**: `https://ton-app.up.railway.app/`

---

**Date de mise à jour**: 2025-12-29
