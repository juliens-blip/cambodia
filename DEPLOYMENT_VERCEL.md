# Déploiement sur Vercel / Railway

## ⚠️ Recommandation: Utiliser Railway.app (Pas Vercel)

**Vercel est optimisé pour Node.js/Next.js**, votre projet étant en Python (FastAPI + Streamlit), utilisez plutôt:

### Option 1: Railway.app (⭐ RECOMMANDÉ)
- ✅ Support Python natif
- ✅ PostgreSQL/Redis inclus
- ✅ Déploiement automatique depuis GitHub
- 💰 **$5-20/mois** (500 heures gratuites au démarrage)

### Option 2: Render.com
- ✅ Support Python natif
- ✅ Free tier disponible
- 💰 **Gratuit** (avec limitations)

---

## 🚀 Déploiement sur Railway.app (Recommandé)

### 1. Installation

```bash
# Installer Railway CLI
npm install -g @railway/cli

# Login
railway login
```

### 2. Créer le Projet

```bash
# Dans votre dossier projet
cd D:\Projects\cambodia

# Initialiser Railway
railway init

# Lier au projet GitHub
railway link
```

### 3. Ajouter les Services

```bash
# Ajouter Redis (cache)
railway add

# Sélectionner "Redis" dans la liste
```

### 4. Configurer les Variables d'Environnement

```bash
# Option A: Via CLI (une par une)
railway variables set SUPABASE_URL=https://xqfozbocgyrelznccweh.supabase.co
railway variables set SUPABASE_ANON_KEY=eyJhbGci...
railway variables set PERPLEXITY_API_KEY=pplx-VOTRE_CLE_ICI

# Option B: Via Dashboard (recommandé)
# 1. Aller sur railway.app/dashboard
# 2. Sélectionner votre projet
# 3. Variables → Copier/coller depuis .env.production
```

#### Variables Essentielles (à configurer):

```env
# SUPABASE (Base de données)
SUPABASE_URL=https://xqfozbocgyrelznccweh.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhxZm96Ym9jZ3lyZWx6bmNjd2VoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY1MTgzODksImV4cCI6MjA4MjA5NDM4OX0.UtpPLJf3JVIN4kPZkjO0iSwzX_-7sqpyzvjo5aObRlw
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhxZm96Ym9jZ3lyZWx6bmNjd2VoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY1MTgzODksImV4cCI6MjA4MjA5NDM4OX0.UtpPLJf3JVIN4kPZkjO0iSwzX_-7sqpyzvjo5aObRlw

# PERPLEXITY (Recherche marché) - ⚠️ REMPLACER PAR VOTRE CLÉ
PERPLEXITY_API_KEY=pplx-VOTRE_VRAIE_CLE_ICI

# GOOGLE DRIVE (Documents)
GOOGLE_DOCS_API_KEY=AIzaSyBL3Q-_cW4dW3BbXhOqbo3F0rtIqJXinyk

# CLAUDE (Mode MOCK)
CLAUDE_MOCK_MODE=true
CLAUDE_API_KEY=mock_key

# ENVIRONMENT
ENVIRONMENT=production
LOG_LEVEL=INFO
SCHEDULER_TIMEZONE=Asia/Phnom_Penh

# COMMODITY CODES
CASHEW_HS_CODE=080130
RUBBER_HS_CODE=400110
```

### 5. Déployer

```bash
# Push automatique depuis GitHub
git push origin main

# Ou déployer manuellement
railway up
```

### 6. Voir les Logs

```bash
railway logs
```

---

## 📊 Si vous voulez vraiment utiliser Vercel (Serverless)

⚠️ **Limitation**: Vercel Serverless Functions ont un timeout de 10 secondes (60s en Pro).

### 1. Créer `vercel.json`

```json
{
  "version": 2,
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ],
  "env": {
    "ENVIRONMENT": "production"
  }
}
```

### 2. Variables d'Environnement sur Vercel

1. Aller sur **vercel.com/dashboard**
2. Sélectionner votre projet
3. **Settings → Environment Variables**
4. Ajouter chaque variable:

```
SUPABASE_URL = https://xqfozbocgyrelznccweh.supabase.co
SUPABASE_ANON_KEY = eyJhbGci...
PERPLEXITY_API_KEY = pplx-VOTRE_CLE
GOOGLE_DOCS_API_KEY = AIzaSyB...
CLAUDE_MOCK_MODE = true
ENVIRONMENT = production
```

### 3. Déployer

```bash
# Installer Vercel CLI
npm install -g vercel

# Login
vercel login

# Déployer
vercel --prod
```

---

## 🔐 Variables à ABSOLUMENT Configurer

| Variable | Où l'obtenir | Obligatoire |
|----------|--------------|-------------|
| `SUPABASE_URL` | Supabase Dashboard | ✅ Oui |
| `SUPABASE_ANON_KEY` | Supabase Dashboard | ✅ Oui |
| `PERPLEXITY_API_KEY` | perplexity.ai/settings | ✅ Oui |
| `GOOGLE_DOCS_API_KEY` | Google Cloud Console | ⚠️ Si vous utilisez Google Drive |
| `CLAUDE_MOCK_MODE` | Mettre `true` | ✅ Oui (pour éviter de payer Claude) |
| `REDIS_URL` | Upstash/Railway | ⚠️ Optionnel (améliore performances) |

---

## 📝 Checklist de Déploiement

- [ ] Variables d'environnement configurées
- [ ] Base de données Supabase accessible
- [ ] Tests API passent (`pytest tests/`)
- [ ] Clé Perplexity valide (tester avec un appel)
- [ ] Mode MOCK Claude activé (`CLAUDE_MOCK_MODE=true`)
- [ ] Logs accessibles pour debugging
- [ ] URL du projet notée pour accès

---

## 💰 Coûts Estimés (par mois)

### Railway.app
- **Hobby**: $5-20/mois (500h gratuites au départ)
- **Pro**: $20-50/mois (selon usage)

### Services Externes
- Supabase: **Gratuit** (jusqu'à 500MB, 2GB bandwidth)
- Perplexity: **$20/mois** (1000 requêtes)
- Upstash Redis: **Gratuit** (10K commandes/jour)

**Total estimé: $25-75/mois**

---

## 🐛 Troubleshooting

### Erreur: "Module not found"
```bash
# Vérifier requirements.txt
railway run pip list

# Réinstaller
railway run pip install -r requirements.txt
```

### Erreur: "Connection timeout" (Supabase)
```bash
# Vérifier que SUPABASE_URL est correct
railway variables get SUPABASE_URL

# Tester la connexion
railway run python -c "from app.services.supabase_service import SupabaseService; print(SupabaseService().test_connection())"
```

### Erreur: "Perplexity API rate limit"
```bash
# Vérifier votre usage
# Activer le cache Redis pour réduire les appels
railway variables set REDIS_URL=redis://...
```

---

## 📞 Support

- Railway: https://railway.app/help
- Supabase: https://supabase.com/docs
- Perplexity: https://docs.perplexity.ai
