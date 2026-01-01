# Guide : Trigger Manuel des Analyses de Marché

Ce guide explique les **3 façons** de déclencher manuellement une analyse de marché pour cashew et/ou rubber.

---

## 🔄 MÉTHODE 1 : Bouton UI (Recommandé)

**Le plus simple - Aucun code nécessaire**

### Étapes :

1. **Ouvrir** Market Trends : https://cambodia.up.railway.app/Market_Trends
2. **Descendre** jusqu'à la section "Trigger New Analysis"
3. **Sélectionner** :
   - Commodity : `Cashew` ou `Rubber`
   - ☑️ Cocher "Force refresh" (pour écraser l'analyse du jour)
4. **Cliquer** : 🚀 **"Trigger New Analysis"**
5. **Attendre** : 10-20 secondes (barre de progression)
6. **Résultat** : Page se rafraîchit automatiquement avec nouvelle analyse

### Avantages :
- ✅ Interface graphique facile
- ✅ Pas de ligne de commande
- ✅ Fonctionne depuis n'importe quel navigateur
- ✅ Disponible immédiatement

---

## 🐍 MÉTHODE 2 : Script Python (Automatisation)

**Pour trigger via ligne de commande ou scripts automatisés**

### Prérequis :

```bash
# Installer httpx si nécessaire
pip install httpx
```

### Usage :

```bash
# Depuis le répertoire du projet
cd D:\Projects\cambodia

# Trigger analyse pour CASHEW + RUBBER
python trigger_analysis.py
```

### Output attendu :

```
============================================================
MARKET ANALYSIS TRIGGER - Cambodia Agri Analytics
Admin Endpoint (No Rate Limit)
============================================================

🚀 Triggering analysis for BOTH...
✅ Analysis trigger successful!
   Status: success
   Message: 2/2 analyses completed
   ✅ CASHEW: 5 tweets, updated 2026-01-01T14:30:00
   ✅ RUBBER: 4 tweets, updated 2026-01-01T14:30:05

============================================================
✅ Analysis complete! Check Market Trends UI.
   https://cambodia.up.railway.app/Market_Trends
============================================================
```

### Personnalisation :

```python
# Modifier trigger_analysis.py ligne 65 pour analyser une seule commodity :

# Pour cashew seulement :
success = trigger_analysis(commodity="cashew")

# Pour rubber seulement :
success = trigger_analysis(commodity="rubber")

# Pour les deux (défaut) :
success = trigger_analysis(commodity=None)
```

### Avantages :
- ✅ Scriptable (cron jobs, automation)
- ✅ Pas de rate limit (endpoint admin)
- ✅ Output détaillé dans terminal
- ✅ Exit code 0 = success, 1 = failure

---

## 🌐 MÉTHODE 3 : API HTTP Direct (Avancé)

**Pour intégration avec d'autres outils (curl, Postman, etc.)**

### Endpoint :

```
POST https://cambodia.up.railway.app/api/v1/admin/trigger-analysis
```

### Paramètres (query string) :

| Paramètre | Type | Valeurs | Description |
|-----------|------|---------|-------------|
| `commodity` | string | `cashew`, `rubber`, ou omis | Commodity à analyser (omis = les deux) |
| `force_refresh` | boolean | `true`, `false` | Force nouvelle analyse même si déjà faite aujourd'hui |

### Exemples :

#### curl (Windows PowerShell) :

```powershell
# Les deux commodities
curl -X POST "https://cambodia.up.railway.app/api/v1/admin/trigger-analysis?force_refresh=true"

# Cashew seulement
curl -X POST "https://cambodia.up.railway.app/api/v1/admin/trigger-analysis?commodity=cashew&force_refresh=true"

# Rubber seulement
curl -X POST "https://cambodia.up.railway.app/api/v1/admin/trigger-analysis?commodity=rubber&force_refresh=true"
```

#### Python `requests` :

```python
import requests

response = requests.post(
    "https://cambodia.up.railway.app/api/v1/admin/trigger-analysis",
    params={"force_refresh": True}
)

print(response.json())
```

#### JavaScript `fetch` :

```javascript
fetch('https://cambodia.up.railway.app/api/v1/admin/trigger-analysis?force_refresh=true', {
    method: 'POST'
})
.then(res => res.json())
.then(data => console.log(data));
```

### Response format :

```json
{
    "status": "success",
    "message": "2/2 analyses completed",
    "results": [
        {
            "commodity": "cashew",
            "status": "success",
            "tweet_count": 5,
            "updated_at": "2026-01-01T14:30:00"
        },
        {
            "commodity": "rubber",
            "status": "success",
            "tweet_count": 4,
            "updated_at": "2026-01-01T14:30:05"
        }
    ]
}
```

### Avantages :
- ✅ Intégration avec n'importe quel langage
- ✅ Pas de rate limit
- ✅ Response JSON structurée
- ✅ Flexible (curl, Postman, scripts)

---

## ⚙️ Configuration Actuelle

### Analyses Automatiques :

| Type | Fréquence | Trigger |
|------|-----------|---------|
| **Startup** | Une fois au démarrage API | Automatique à chaque redéploiement |
| **Quotidien** | Tous les jours à 09:00 Cambodia (02:00 UTC) | APScheduler |

### Analyses Manuelles :

| Méthode | Rate Limit | Recommandation |
|---------|------------|----------------|
| **UI Button** | Oui (50/heure) | Usage normal |
| **Admin Endpoint** | Non | Scripts, automation |

---

## 🐛 Troubleshooting

### Erreur 403 Forbidden (UI Button)

**Cause** : Rate limit dépassé (50 requêtes/heure)

**Solution** : Utiliser le script Python (endpoint admin sans rate limit)

### Erreur "Analysis already exists for today"

**Cause** : Une analyse a déjà été faite aujourd'hui

**Solution** : Cocher "Force refresh" dans l'UI ou passer `force_refresh=true` via API

### Script Python échoue avec SSL error

**Normal** : Le script utilise `verify=False` pour contourner les problèmes SSL Windows

**Si besoin** : Installer certificats via `pip install certifi`

### Analyses ne se mettent pas à jour dans l'UI

**Solution** :
1. Rafraîchir la page (F5)
2. Vider cache navigateur (Ctrl+Shift+R)
3. Vérifier Railway logs pour confirmation exécution

---

## 📊 Vérification Post-Analyse

Après avoir triggé une analyse, vérifiez :

1. **Market Trends UI** :
   - Date updated = aujourd'hui
   - Tweet count \u003e 0
   - Analyses générées (pessimistic, realistic, optimistic)

2. **Railway Logs** :
   - Rechercher `[ADMIN] Analyzing cashew...`
   - Rechercher `[ADMIN] ✅ cashew analysis completed`

3. **Supabase** :
   - Table `market_trends` contient nouvelles lignes
   - `trend_date` = aujourd'hui

---

## 📝 Notes Importantes

- 💰 **Coût** : Chaque analyse = $0.005 (Perplexity API)
- ⏱️ **Durée** : 10-20 secondes par commodity
- 🔄 **Quotidien** : Analyses automatiques tous les jours à 09:00 Cambodia
- 🚀 **Startup** : Nouvelle analyse à chaque redéploiement Railway

---

*Documentation mise à jour : 2026-01-01*
*Endpoint admin disponible depuis commit : 8156fc0*
