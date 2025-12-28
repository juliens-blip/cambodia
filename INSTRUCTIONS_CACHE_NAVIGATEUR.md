# 🔧 Instructions: Vider le Cache du Navigateur

**Date:** 2025-12-27
**Problème:** Erreurs 404 sur `_stcore/health` et `_stcore/host-config`

---

## 🎯 Pourquoi Vider le Cache?

Les noms de fichiers ont changé (suppression des emojis):
- **AVANT:** `6_📊_Scenario_Analysis.py` → URL: `/📊_Scenario_Analysis/...`
- **APRÈS:** `6_Scenario_Analysis.py` → URL: `/Scenario_Analysis/...`

Le navigateur a **mis en cache les anciennes URLs** qui ne fonctionnent plus!

---

## ✅ SOLUTION 1: Hard Refresh (Recommandé)

### Sur Windows / Linux:
```
1. Aller sur: http://localhost:8501
2. Appuyer simultanément sur: Ctrl + Shift + R
3. Attendre que la page se recharge complètement
```

### Sur Mac:
```
1. Aller sur: http://localhost:8501
2. Appuyer simultanément sur: Cmd + Shift + R
3. Attendre que la page se recharge complètement
```

---

## ✅ SOLUTION 2: DevTools (Si Solution 1 ne marche pas)

### Chrome / Edge:
```
1. F12 pour ouvrir DevTools
2. Clic-DROIT sur le bouton Refresh ⟳ (à côté de l'URL)
3. Sélectionner: "Empty Cache and Hard Reload"
4. Attendre le rechargement
5. Fermer DevTools (F12)
```

### Firefox:
```
1. F12 pour ouvrir DevTools
2. Clic-droit sur le bouton Refresh
3. Sélectionner: "Empty Cache and Hard Reload"
4. Attendre le rechargement
```

---

## ✅ SOLUTION 3: Vider Complètement le Cache (Nucléaire)

### Chrome / Edge:
```
1. Ctrl + Shift + Delete (ouvre les paramètres de nettoyage)
2. Sélectionner:
   - Période: "Dernière heure" (ou "Tout")
   - Cocher: "Images et fichiers en cache"
3. Cliquer sur "Effacer les données"
4. Rouvrir: http://localhost:8501
```

### Firefox:
```
1. Ctrl + Shift + Delete
2. Sélectionner:
   - Période: "Dernière heure"
   - Cocher: "Cache"
3. Cliquer sur "Effacer maintenant"
4. Rouvrir: http://localhost:8501
```

---

## ✅ SOLUTION 4: Mode Navigation Privée (Test)

Pour tester sans vider le cache principal:

```
1. Ouvrir une fenêtre de navigation privée:
   - Chrome/Edge: Ctrl + Shift + N
   - Firefox: Ctrl + Shift + P

2. Aller sur: http://localhost:8501

3. Tester Scenario Analysis
```

**Si ça marche en navigation privée** → Le problème est bien le cache!
→ Retourner à la Solution 1, 2 ou 3.

---

## 🧪 Comment Vérifier que ça Marche?

### AVANT (avec cache corrompu):
```javascript
Console (F12):
❌ GET http://localhost:8501/Scenario_Analysis/_stcore/health 404
❌ GET http://localhost:8501/Scenario_Analysis/_stcore/host-config 404
❌ Errors en rouge
```

### APRÈS (cache vidé):
```javascript
Console (F12):
✅ Aucune erreur 404
✅ GET http://localhost:8501/_stcore/health 200
✅ GET http://localhost:8501/_stcore/host-config 200
✅ WebSocket connecté
```

---

## 🔍 Si Ça Ne Marche TOUJOURS Pas

### Vérifier les Services:

```bash
# Tester l'API
curl http://localhost:8000/health
# Devrait retourner: {"status":"healthy",...}

# Tester Streamlit
curl http://localhost:8501
# Devrait retourner: HTML de Streamlit
```

### Redémarrer les Services:

**Option A: Redémarrer TOUT**
```bash
# Tuer tous les processus Python
taskkill /F /IM python.exe

# Redémarrer API
cd D:\Projects\cambodia
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Redémarrer Streamlit (autre terminal)
python -m streamlit run ui/streamlit_app.py --server.port 8501
```

**Option B: Redémarrer Streamlit uniquement**
```bash
# Trouver le PID de Streamlit
ps aux | grep streamlit

# Tuer le processus
kill -9 <PID>

# Redémarrer
cd D:\Projects\cambodia
python -m streamlit run ui/streamlit_app.py --server.port 8501
```

---

## 📊 État Actuel des Services

**Services qui tournent:**
- ✅ API Backend: http://localhost:8000 (healthy)
- ✅ Streamlit UI: http://localhost:8501 (200 OK)

**Pages disponibles:**
- ✅ Search
- ✅ AI QA
- ✅ History
- ✅ Admin
- ✅ Market Trends
- ✅ **Scenario Analysis** ← Celle qui pose problème

---

## 🎯 Action Immédiate

**FAITES MAINTENANT:**

1. **Fermez tous les onglets** http://localhost:8501
2. **Faites Ctrl + Shift + R** sur le navigateur
3. **Ouvrez un NOUVEL onglet**: http://localhost:8501
4. **Ouvrez F12** (Console)
5. **Allez sur Scenario Analysis**
6. **Vérifiez la console** → Plus d'erreurs 404?

**Si ça marche:**
✅ Le cache est vidé, tout est bon!

**Si ça ne marche toujours pas:**
→ Passez à la Solution 2 (DevTools)
→ Ou Solution 3 (Vider complètement le cache)
→ Ou demandez-moi de redémarrer les services

---

## 💡 Pourquoi Ce Problème Arrive

**Streamlit génère des URLs basées sur les noms de fichiers:**

```python
# Nom fichier: 6_📊_Scenario_Analysis.py
# URL générée: /📊_Scenario_Analysis
# Assets: /📊_Scenario_Analysis/_stcore/health ❌

# Nom fichier: 6_Scenario_Analysis.py
# URL générée: /Scenario_Analysis
# Assets: /_stcore/health ✅
```

Le navigateur a **caché l'ancienne URL avec l'emoji**, et continue d'essayer de charger:
```
/Scenario_Analysis/_stcore/health  (au lieu de /_stcore/health)
```

**Solution permanente appliquée:**
- ✅ Tous les fichiers renommés sans emojis
- ✅ Plus de problème à l'avenir

**Mais le cache existant doit être vidé manuellement!**

---

**Créé par:** Claude Code (Debugger Mode)
**Date:** 2025-12-27
**Action requise:** ⚠️ **HARD REFRESH OBLIGATOIRE** (Ctrl+Shift+R)
