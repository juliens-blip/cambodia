# 🚂 Railway - Configuration Simplifiée

## ✅ Configuration Actuelle

Railway va maintenant détecter automatiquement Python avec:

1. **runtime.txt** → Spécifie Python 3.11.9
2. **Procfile** → Commande de démarrage
3. **requirements.txt** → Dépendances Python

**Pas besoin de railway.toml ou nixpacks!**

---

## 🔧 Instructions de Déploiement

### 1. Sur Railway Dashboard:

1. Aller sur https://railway.app/dashboard
2. Sélectionner votre projet `cambodia`
3. **Settings** → **Redeploy** → Cliquer sur "Redeploy"

### 2. Vérifier les Variables d'Environnement

**Variables** tab → Vérifier que vous avez:

```env
SUPABASE_URL=https://xqfozbocgyrelznccweh.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhxZm96Ym9jZ3lyZWx6bmNjd2VoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY1MTgzODksImV4cCI6MjA4MjA5NDM4OX0.UtpPLJf3JVIN4kPZkjO0iSwzX_-7sqpyzvjo5aObRlw
PERPLEXITY_API_KEY=pplx-VOTRE_CLE_ICI
GOOGLE_DOCS_API_KEY=AIzaSyBL3Q-_cW4dW3BbXhOqbo3F0rtIqJXinyk
CLAUDE_MOCK_MODE=true
ENVIRONMENT=production
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
SCHEDULER_TIMEZONE=Asia/Phnom_Penh
CASHEW_HS_CODE=080130
RUBBER_HS_CODE=400110
```

⚠️ **IMPORTANT**: Remplacer `PERPLEXITY_API_KEY` par votre vraie clé!

### 3. Voir les Logs

**Deployments** → Dernier déploiement → **View Logs**

Vous devriez voir:
```
Installing Python 3.11.9
Installing dependencies from requirements.txt
Starting application with uvicorn
```

### 4. Tester l'API

Une fois déployé:
- Aller sur: `https://VOTRE_APP.up.railway.app/docs`
- Vous devriez voir la documentation Swagger de FastAPI

---

## 🐛 Si ça ne marche toujours pas:

### Option A: Désactiver les dépendances problématiques

Créer `requirements-railway.txt`:

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
supabase==2.3.0
httpx==0.26.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
```

Puis dans Railway **Settings** → **Build Command**:
```
pip install -r requirements-railway.txt
```

### Option B: Utiliser Docker

Railway supporte Docker. Si Python natif ne marche pas, on peut créer un Dockerfile.

---

## ❌ Pourquoi Vercel ne marche PAS:

```
Error: Serverless Function exceeded 250 MB
```

Votre projet fait **~400-500 MB** à cause de:
- ChromaDB: ~150 MB
- Streamlit: ~80 MB
- Plotly: ~50 MB
- Tesseract data: ~20 MB
- Autres dépendances: ~200 MB

**Vercel = Impossible pour ce projet!**

---

## ✅ Prochaines Étapes

1. Push les changements sur GitHub
2. Railway redéploiera automatiquement
3. Vérifier les logs
4. Tester l'API

**Let's go! 🚀**
