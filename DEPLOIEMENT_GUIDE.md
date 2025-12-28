# 🚀 Guide de Déploiement - Cambodia Agri Analytics

## ⚠️ IMPORTANT: Vercel vs Railway

### ❌ Pourquoi PAS Vercel pour ce projet?

1. **Timeout 10 secondes** (60s en Pro) - Trop court pour:
   - Scraping ODC (20-30 secondes)
   - Génération rapports Perplexity (15-25 secondes)
   - Processing PDF OCR (10-40 secondes)

2. **Pas de support Tesseract/Poppler** (OCR)
   - Tesseract requis pour PDF khmer → anglais
   - Poppler requis pour conversion PDF

3. **Serverless Functions** - Pas adapté pour:
   - Scheduler APScheduler (jobs quotidiens/hebdomadaires)
   - ChromaDB embedded
   - Long-running processes

4. **Limites mémoire** strictes (1GB)

### ✅ Pourquoi Railway.app?

1. **Support Python natif** avec buildpacks Nixpacks
2. **Pas de timeout** pour les long-running processes
3. **APScheduler fonctionne** (cron jobs)
4. **Tesseract/Poppler inclus** dans nixpacks
5. **Redis/PostgreSQL intégrés**
6. **Logs en temps réel**
7. **500 heures gratuites** au démarrage

---

## 🚂 Option 1: Railway.app (⭐ RECOMMANDÉ)

### Étape 1: Créer un compte

1. Aller sur https://railway.app
2. **Sign up with GitHub**
3. Autoriser Railway à accéder à vos repos

### Étape 2: Créer un nouveau projet

1. **New Project** → **Deploy from GitHub repo**
2. Sélectionner `juliens-blip/cambodia`
3. Railway va détecter automatiquement Python

### Étape 3: Configurer les Variables d'Environnement

Dans le dashboard Railway:

1. Cliquer sur votre projet
2. **Variables** (onglet)
3. **Raw Editor** → Coller ceci:

```env
# SUPABASE
SUPABASE_URL=https://xqfozbocgyrelznccweh.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhxZm96Ym9jZ3lyZWx6bmNjd2VoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY1MTgzODksImV4cCI6MjA4MjA5NDM4OX0.UtpPLJf3JVIN4kPZkjO0iSwzX_-7sqpyzvjo5aObRlw
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhxZm96Ym9jZ3lyZWx6bmNjd2VoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY1MTgzODksImV4cCI6MjA4MjA5NDM4OX0.UtpPLJf3JVIN4kPZkjO0iSwzX_-7sqpyzvjo5aObRlw

# PERPLEXITY (⚠️ REMPLACER PAR VOTRE VRAIE CLÉ)
PERPLEXITY_API_KEY=pplx-VOTRE_VRAIE_CLE_ICI
PERPLEXITY_CACHE_TTL=86400
PERPLEXITY_MAX_REQUESTS_PER_MONTH=1000

# GOOGLE DRIVE
GOOGLE_DOCS_API_KEY=AIzaSyBL3Q-_cW4dW3BbXhOqbo3F0rtIqJXinyk

# CLAUDE (MOCK MODE)
CLAUDE_MOCK_MODE=true
CLAUDE_API_KEY=mock_key

# APPLICATION
ENVIRONMENT=production
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1

# SCHEDULER
SCHEDULER_TIMEZONE=Asia/Phnom_Penh
DAILY_COLLECTION_HOUR=6
WEEKLY_ANALYSIS_DAY=monday
WEEKLY_ANALYSIS_HOUR=6

# COMMODITY
CASHEW_HS_CODE=080130
RUBBER_HS_CODE=400110

# URLS
MEF_API_URL=http://www.mef.gov.kh/api
WITS_API_URL=https://wits.worldbank.org/API/V1
ODC_API_URL=https://data.opendevelopmentcambodia.net/api/3
```

4. **⚠️ IMPORTANT**: Remplacer `PERPLEXITY_API_KEY` par votre vraie clé

### Étape 4: Ajouter Redis (Optionnel mais recommandé)

1. Dans votre projet Railway: **+ New** → **Database** → **Add Redis**
2. Railway va auto-créer la variable `REDIS_URL`
3. Rien d'autre à faire!

### Étape 5: Déployer

1. Railway va automatiquement déployer à chaque `git push`
2. Voir les logs: **Deployments** → Cliquer sur le déploiement en cours
3. Votre API sera disponible sur: `https://votre-app.railway.app`

### Étape 6: Obtenir l'URL publique

1. **Settings** → **Networking** → **Generate Domain**
2. Copier l'URL: `https://cambodia-production.up.railway.app`
3. Tester: `https://cambodia-production.up.railway.app/docs` (FastAPI Swagger)

---

## 📊 Option 2: Vercel (⚠️ Limitations importantes)

### Problèmes que vous rencontrerez:

- ❌ Timeout sur scraping ODC
- ❌ Pas de Tesseract OCR (PDF processing échouera)
- ❌ APScheduler ne fonctionnera pas (pas de cron jobs)
- ❌ ChromaDB embedded ne fonctionnera pas

### Si vous insistez quand même:

1. **Configurer les variables sur Vercel:**
   - Dashboard Vercel → Votre projet → **Settings** → **Environment Variables**
   - Coller les mêmes variables que Railway ci-dessus

2. **Déployer:**
   ```bash
   vercel --prod
   ```

3. **Limiter les fonctionnalités:**
   - Désactiver APScheduler (pas de cron jobs automatiques)
   - Désactiver PDF OCR (pas de Tesseract)
   - Utiliser ChromaDB Cloud (pas embedded)
   - Réduire timeout des scrapers

---

## 🔑 Où obtenir vos clés API?

### Perplexity API
1. https://www.perplexity.ai/settings/api
2. **Create API Key**
3. Copier la clé: `pplx-xxxxxxxxxxxxxxxx`
4. **Coût**: ~$20/mois (1000 requêtes)

### Supabase (Déjà configuré)
- URL: `https://xqfozbocgyrelznccweh.supabase.co`
- Keys disponibles dans: https://supabase.com/dashboard/project/xqfozbocgyrelznccweh/settings/api

### Google Drive API (Optionnel)
1. https://console.cloud.google.com
2. **APIs & Services** → **Credentials**
3. **Create Credentials** → **API Key**

---

## ✅ Checklist de Déploiement

- [ ] Compte Railway créé
- [ ] Projet GitHub connecté
- [ ] Variables d'environnement configurées
- [ ] **PERPLEXITY_API_KEY** remplacé par vraie clé
- [ ] Redis ajouté (optionnel)
- [ ] Déploiement réussi (voir logs)
- [ ] URL publique générée
- [ ] Test API: `/docs` accessible
- [ ] Test endpoint: `/api/prices` fonctionne

---

## 🐛 Troubleshooting

### Erreur: "Module not found"
```bash
# Vérifier que requirements.txt est bien lu
# Railway logs devrait montrer:
# "Installing from requirements.txt"
```

### Erreur: "Database connection failed"
```bash
# Vérifier SUPABASE_URL dans les variables
# Test manuel:
curl https://xqfozbocgyrelznccweh.supabase.co/rest/v1/
```

### Erreur: "Perplexity rate limit"
```bash
# Vérifier votre usage Perplexity:
# https://www.perplexity.ai/settings/api
# Activer Redis cache pour réduire les appels
```

### Logs ne s'affichent pas
```bash
# Ajouter PYTHONUNBUFFERED=1 dans les variables
```

---

## 💰 Coûts Mensuels

### Railway
- **Hobby**: $5-20/mois
- **500 heures gratuites** au démarrage
- **$10 de crédit gratuit** au signup

### Services Externes
- Supabase: **Gratuit** (Free tier)
- Perplexity: **$20/mois** (1000 requêtes)
- Upstash Redis: **Gratuit** (10K commandes/jour)

**Total: ~$25-40/mois** (après crédit gratuit épuisé)

---

## 📞 Support

- **Railway**: https://railway.app/help
- **Supabase**: https://supabase.com/docs
- **Perplexity**: https://docs.perplexity.ai

---

## 🎯 Prochaines Étapes

1. ✅ Déployer sur Railway
2. ✅ Tester les endpoints API
3. ✅ Vérifier les cron jobs APScheduler
4. ✅ Monitorer l'usage Perplexity
5. ✅ Configurer alertes (optionnel)

**Bon déploiement! 🚀**
