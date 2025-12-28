# 🔐 Variables d'Environnement Railway - CONFIGURATION EXACTE

## ⚠️ IMPORTANT: Noms des Variables

Le fichier `app/config.py` attend ces noms **EXACTS** (Pydantic convertit en majuscules):

---

## ✅ Variables OBLIGATOIRES

Copiez-collez EXACTEMENT ces variables dans Railway:

```env
# SUPABASE (Base de données)
SUPABASE_URL=https://xqfozbocgyrelznccweh.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhxZm96Ym9jZ3lyZWx6bmNjd2VoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY1MTgzODksImV4cCI6MjA4MjA5NDM4OX0.UtpPLJf3JVIN4kPZkjO0iSwzX_-7sqpyzvjo5aObRlw

# PERPLEXITY (⚠️ REMPLACER PAR VOTRE VRAIE CLÉ)
PERPLEXITY_API_KEY=pplx-VOTRE_VRAIE_CLE_ICI

# GOOGLE DRIVE (Obligatoire même si vous ne l'utilisez pas)
GOOGLE_DRIVE_API_KEY=AIzaSyBL3Q-_cW4dW3BbXhOqbo3F0rtIqJXinyk

# CLAUDE (Mock mode - pas besoin de vraie clé)
CLAUDE_MOCK_MODE=true

# APPLICATION
PYTHONUNBUFFERED=1
DEBUG=false
```

---

## 🔄 Correspondance des Variables

| ❌ Ancien Nom (Incorrect) | ✅ Nouveau Nom (Correct) |
|---------------------------|--------------------------|
| `SUPABASE_ANON_KEY` | `SUPABASE_KEY` |
| `GOOGLE_DOCS_API_KEY` | `GOOGLE_DRIVE_API_KEY` |

---

## 📋 Comment Configurer dans Railway

### Méthode 1: Raw Editor (RECOMMANDÉ)

1. Railway Dashboard → Votre projet → **Variables**
2. Cliquer sur **Raw Editor**
3. **SUPPRIMER TOUT** le contenu actuel
4. **COLLER** exactement ceci:

```env
SUPABASE_URL=https://xqfozbocgyrelznccweh.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhxZm96Ym9jZ3lyZWx6bmNjd2VoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY1MTgzODksImV4cCI6MjA4MjA5NDM4OX0.UtpPLJf3JVIN4kPZkjO0iSwzX_-7sqpyzvjo5aObRlw
PERPLEXITY_API_KEY=pplx-VOTRE_VRAIE_CLE_ICI
GOOGLE_DRIVE_API_KEY=AIzaSyBL3Q-_cW4dW3BbXhOqbo3F0rtIqJXinyk
CLAUDE_MOCK_MODE=true
PYTHONUNBUFFERED=1
DEBUG=false
```

5. **Update Variables**
6. Railway va automatiquement **redéployer**

### Méthode 2: Une par une

Cliquer **+ New Variable** et ajouter:

| Variable | Valeur |
|----------|--------|
| `SUPABASE_URL` | `https://xqfozbocgyrelznccweh.supabase.co` |
| `SUPABASE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhxZm96Ym9jZ3lyZWx6bmNjd2VoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY1MTgzODksImV4cCI6MjA4MjA5NDM4OX0.UtpPLJf3JVIN4kPZkjO0iSwzX_-7sqpyzvjo5aObRlw` |
| `PERPLEXITY_API_KEY` | `pplx-VOTRE_CLE` |
| `GOOGLE_DRIVE_API_KEY` | `AIzaSyBL3Q-_cW4dW3BbXhOqbo3F0rtIqJXinyk` |
| `CLAUDE_MOCK_MODE` | `true` |
| `PYTHONUNBUFFERED` | `1` |

---

## ⚠️ NE PAS OUBLIER

**Remplacer `PERPLEXITY_API_KEY`** par votre vraie clé:
1. Aller sur https://www.perplexity.ai/settings/api
2. Créer une API Key
3. Copier et remplacer `pplx-VOTRE_VRAIE_CLE_ICI`

---

## ✅ Vérification

Après avoir configuré les variables:

1. Railway va **automatiquement redéployer**
2. Aller dans **Deployments** → Dernier déploiement
3. **View Logs** → Vous devriez voir:

```
✅ Installing Python 3.11.9
✅ Installing dependencies from requirements.txt
✅ Starting uvicorn app.main:app
✅ Uvicorn running on http://0.0.0.0:8000
```

4. Tester votre URL: `https://VOTRE_APP.up.railway.app/docs`

---

## 🐛 Si ça ne marche toujours pas

Vérifier dans les logs Railway que vous voyez bien:
```python
Settings loaded successfully
supabase_url: https://xqfozbocgyrelznccweh.supabase.co
supabase_key: eyJhbGci... (masqué)
```

Si vous voyez encore:
```
ValidationError: Field required
```

→ La variable n'est PAS configurée dans Railway. Revérifier les noms!

---

## 📞 Prochaines Étapes

1. Configurer les variables comme ci-dessus
2. Attendre le redéploiement automatique (~2-3 minutes)
3. Vérifier les logs
4. Tester l'API

**C'est parti! 🚀**
