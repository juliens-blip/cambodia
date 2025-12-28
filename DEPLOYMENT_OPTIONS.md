# OPTIONS DE DÉPLOIEMENT - CAMBODIA AGRI ANALYTICS

## ⚠️ IMPORTANT : VERCEL NE SUPPORTE PAS PYTHON

**Vercel est uniquement pour Next.js/Node.js**. Pour Python + FastAPI + Streamlit, voici les vraies options :

---

## TEST PRODUCTION (1 JOURNÉE)

### Option 1 : Local (PC Allumé) ⭐ RECOMMANDÉ POUR TEST
**Coût** : Gratuit
**Setup** : 15 minutes

```bash
# Docker Compose local
docker-compose up -d

# Accès
- API: http://localhost:8000
- Dashboard: http://localhost:8501
- Ngrok tunnel (pour partager): ngrok http 8501
```

**Pros** :
- ✅ Gratuit
- ✅ Contrôle total
- ✅ Debugging facile

**Cons** :
- ❌ PC doit rester allumé
- ❌ Pas d'accès public (sauf ngrok)
- ❌ Pas de monitoring

---

### Option 2 : Render.com Free Tier
**Coût** : Gratuit (750h/mois)
**Setup** : 30 minutes

**Limitations Free Tier** :
- App s'endort après 15min inactivité
- 512MB RAM (peut être tight pour Streamlit)
- 1 instance seulement

**Steps** :
1. Créer compte Render.com
2. New Web Service → Import GitHub repo
3. Environment: Docker
4. Add env variables
5. Deploy (auto-deploy on git push)

**Pros** :
- ✅ Gratuit
- ✅ HTTPS automatique
- ✅ Git-based deployment
- ✅ Logs en temps réel

**Cons** :
- ❌ Sleep après inactivité (first request lent)
- ❌ RAM limitée
- ❌ 1 seul service (API + Dashboard sur même instance)

---

### Option 3 : Railway.app
**Coût** : $5 crédit gratuit/mois → ~500h usage
**Setup** : 20 minutes

**Inclusions** :
- PostgreSQL managed (gratuit avec crédit)
- Redis cache
- Auto-scaling

**Steps** :
1. Signup Railway.app
2. New Project → Deploy from GitHub
3. Add PostgreSQL + Redis services
4. Configure env variables
5. Deploy

**Pros** :
- ✅ $5 crédit gratuit (suffisant pour test)
- ✅ Postgres + Redis inclus
- ✅ Pas de sleep (instance toujours active)
- ✅ Meilleur que Render pour multi-services

**Cons** :
- ❌ Après $5, payant (mais ~$10/mois raisonnable)

---

## PRODUCTION (LONG-TERME)

### Comparaison Plateformes

| Plateforme | Coût/Mois | RAM | Postgres | Redis | Auto-deploy | Notes |
|------------|-----------|-----|----------|-------|-------------|-------|
| **Render.com** | $7 (Starter) | 1GB | $7 (512MB) | Via Upstash | ✅ Git | Simple, docs excellentes |
| **Railway.app** | $10-15 | 1GB | Inclus | Inclus | ✅ Git | Best value, tout inclus |
| **Fly.io** | $6-10 | 1GB | $2 (1GB) | Via Upstash | ✅ Git | Plus technique, bon pricing |
| **DigitalOcean VPS** | $12 | 2GB | Self-hosted | Self-hosted | ❌ Manual | Contrôle total, plus work |
| **Streamlit Cloud** | $20 | 1GB | ❌ | ❌ | ✅ Git | ⚠️ Streamlit only (no FastAPI) |

---

### RECOMMANDATION FINALE

#### Pour Test (1 journée) :
**🥇 Railway.app** ($5 crédit gratuit)
- Raison : Pas de sleep, Postgres inclus, facile setup

**🥈 Local + ngrok** (si budget zéro absolu)
- Raison : Gratuit, mais PC doit rester allumé

#### Pour Production :
**🥇 Railway.app** ($10-15/mois)
- Raison : Meilleur rapport qualité/prix, tout inclus (Postgres, Redis, monitoring)
- Inconvénient : Coût variable (pay-as-you-go)

**🥈 Render.com** ($14/mois = $7 app + $7 Postgres)
- Raison : Pricing fixe, docs excellentes
- Inconvénient : Besoin Upstash Redis séparé (~$10/mois)

**🥉 Fly.io** ($8-12/mois)
- Raison : Bon pricing, multi-région
- Inconvénient : Plus technique, CLI-first

---

## ARCHITECTURE DEPLOYMENT RECOMMANDÉE

### Railway.app (Production)

```yaml
# railway.json
{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE"
  }
}
```

**Services Railway** :
1. **App (FastAPI + APScheduler)**
   - Dockerfile: API service
   - Port: 8000
   - Env: SUPABASE_URL, PERPLEXITY_KEY, CLAUDE_KEY, etc.

2. **Dashboard (Streamlit)**
   - Dockerfile: Dashboard service
   - Port: 8501
   - Dépend de: App (API calls)

3. **PostgreSQL** (managed)
   - Fourni par Railway
   - Connexion: DATABASE_URL auto-injectée

4. **Redis** (managed)
   - Fourni par Railway
   - Connexion: REDIS_URL auto-injectée

**Deployment Flow** :
```
git push → Railway auto-detect Dockerfile → Build → Deploy → Health check → Live
```

---

## ALTERNATIVE : SUPABASE EDGE FUNCTIONS (BONUS)

Pour réduire coûts, on peut mettre certains jobs en **Supabase Edge Functions** (serverless Deno) :

**Candidates** :
- Daily collection jobs (trigger cron)
- Perplexity API calls (stateless)
- Claude report generation

**Avantages** :
- Gratuit jusqu'à 500k invocations/mois
- Pas de serveur à maintenir
- Auto-scaling

**Inconvénients** :
- Deno (TypeScript), pas Python
- Cold starts (1-2s)
- Besoin réécrire collecteurs en TS

**Verdict** : Possible Phase 2, mais MVP reste Python on Railway/Render.

---

## PLAN DE MIGRATION

### Semaine 4 : Test Local
- Docker Compose sur PC
- Validation complète
- Ngrok pour demo

### Semaine 4 (fin) : Test Production
- Deploy Railway.app
- Test 24h avec vraies données
- Monitoring uptime

### Semaine 5+ : Production
- Si test OK → Keep Railway
- Si budget serré → Migrate Fly.io
- Si besoin scale → VPS DigitalOcean + Terraform

---

## COÛTS PROJETÉS (12 MOIS)

### Scénario 1 : Railway.app
- Hosting: $15/mois × 12 = $180/an
- Supabase Pro: $25/mois × 12 = $300/an (si >500MB data)
- Perplexity API: $20/mois × 12 = $240/an
- Claude API: $10/mois × 12 = $120/an (estimation)
- **TOTAL** : $840/an (~$70/mois)

### Scénario 2 : VPS DigitalOcean
- VPS 2GB: $12/mois × 12 = $144/an
- Supabase: $300/an
- APIs: $360/an (Perplexity + Claude)
- **TOTAL** : $804/an (~$67/mois)
- Économie : $36/an (mais + maintenance manuelle)

---

## DÉCISION FINALE

**TEST** : Railway.app (gratuit avec $5 crédit)
**PRODUCTION** : Railway.app ($70/mois all-in)

**Raison** : Simplicité > Économie marginale. Temps économisé sur DevOps > $3/mois saved.
