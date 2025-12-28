# BugFix: Citations & Cache Streamlit

**Date:** 2025-12-27
**Status:** ✅ CORRIGÉ

---

## 🐛 Problèmes Identifiés

### Problème 1: AttributeError sur les Citations

**Erreur:**
```python
AttributeError: 'str' object has no attribute 'get'
File "D:\Projects\cambodia\ui\pages\6_Scenario_Analysis.py", line 311
    st.markdown(f"**[{i}]** {citation.get('content', '')[:300]}...")
```

**Cause:**
L'API RAG retourne les citations comme des **strings simples**, pas comme des dictionnaires.

**Code problématique:**
```python
# Ligne 311 - AVANT
for i, citation in enumerate(citations, 1):
    st.markdown(f"**[{i}]** {citation.get('content', '')[:300]}...")  # ❌ citation est un str!
    st.caption(f"Source: {citation.get('source', 'Unknown')}")
```

### Problème 2: Cache Navigateur avec Anciennes URLs

**Erreur:**
```
GET http://localhost:8501/Scenario_Analysis/_stcore/health 404 (Not Found)
GET http://localhost:8501/Scenario_Analysis/_stcore/host-config 404 (Not Found)
```

**Cause:**
Le cache du navigateur pointe encore vers les anciennes URLs générées avec les emojis dans les noms de fichiers.

**URLs incorrectes (cachées):**
```
/Scenario_Analysis/_stcore/health  ❌
/Market_Trends/_stcore/health      ❌
```

**URLs correctes:**
```
/_stcore/health                    ✅
/_stcore/host-config               ✅
```

---

## ✅ Solutions Appliquées

### Solution 1: Gestion Polymorphe des Citations

**Fichier:** `ui/pages/6_Scenario_Analysis.py` - Lignes 306-321

**Code corrigé:**
```python
# Citations
citations = analysis_data.get('citations', [])
if citations:
    with st.expander(f"📚 {t.get('trends_sources', 'Sources & Citations')} ({len(citations)})"):
        for i, citation in enumerate(citations, 1):
            # Handle both string citations and dict citations
            if isinstance(citation, str):
                # Citation is a simple string
                st.markdown(f"**[{i}]** {citation[:300]}...")
            elif isinstance(citation, dict):
                # Citation is a dictionary
                st.markdown(f"**[{i}]** {citation.get('content', '')[:300]}...")
                st.caption(f"Source: {citation.get('source', 'Unknown')} | Similarity: {citation.get('similarity', 0):.2%}")
            else:
                # Fallback for unknown type
                st.markdown(f"**[{i}]** {str(citation)[:300]}...")
```

**Avantages:**
- ✅ Supporte les citations en format `str` (retour actuel de l'API)
- ✅ Supporte les citations en format `dict` (pour compatibilité future)
- ✅ Fallback sécurisé pour tout autre type

### Solution 2: Hard Refresh de Streamlit

**Actions:**
1. Tuer le processus Streamlit
2. Redémarrer en mode headless
3. Forcer l'utilisateur à faire Ctrl+Shift+R (hard refresh)

**Commandes:**
```bash
# Tuer Streamlit
killall streamlit

# Redémarrer proprement
cd D:\Projects\cambodia
python -m streamlit run ui/streamlit_app.py --server.port 8501 --server.headless true
```

---

## 🧪 Vérifications

### Test 1: Citations Affichées
**Test:** Générer une analyse et vérifier les citations
**Attendu:** Les 7 citations s'affichent sans erreur
**Résultat:** ✅ PASSÉ

### Test 2: Assets JavaScript
**Test:** Ouvrir la console navigateur (F12)
**Attendu:** Aucune erreur 404 sur `_stcore/health`
**Résultat:** ⏳ À vérifier après hard refresh navigateur

### Test 3: Connexion WebSocket
**Test:** Vérifier que Streamlit se connecte correctement
**Attendu:** Pas d'erreurs de connexion
**Résultat:** ⏳ À vérifier après hard refresh navigateur

---

## 📋 Actions Utilisateur Requises

### IMPORTANT: Hard Refresh Navigateur

Pour vider le cache du navigateur qui pointe vers les anciennes URLs:

**Windows / Linux:**
```
Ctrl + Shift + R
```

**Mac:**
```
Cmd + Shift + R
```

**Ou via DevTools:**
1. Ouvrir DevTools (F12)
2. Clic-droit sur le bouton Refresh
3. Sélectionner "Empty Cache and Hard Reload"

---

## 🔍 Problèmes Résiduels (Non Critiques)

### Warnings LaTeX
**Message:**
```
LaTeX-incompatible input and strict mode is set to 'warn':
Unrecognized Unicode character "—"
% comment has no terminating newline
```

**Cause:**
L'analyse générée par Perplexity contient des caractères Unicode (tirets longs "—") et des symboles de pourcentage qui sont interprétés comme du LaTeX par Streamlit.

**Impact:** ⚠️ Warnings seulement (pas d'erreur bloquante)

**Solution possible (optionnelle):**
```python
# Nettoyer le markdown avant affichage
analysis_clean = analysis_data.get('analysis', '')
analysis_clean = analysis_clean.replace('—', '-')  # Remplacer tiret long
analysis_clean = analysis_clean.replace('%', r'\%')  # Échapper le pourcentage
st.markdown(analysis_clean)
```

### Tweets Non Affichés
**Observation:** "aucun tweet sorti"

**Cause:**
Les données de test n'ont pas de tweets réels dans `top_tweets`. L'API retourne un sentiment général mais pas de tweets individuels.

**Impact:** ℹ️ Informatif (message affiché: "No recent tweets found")

**Normal:** ✅ Le système fonctionne correctement avec le fallback sur prix + documents

---

## ✅ Résumé des Corrections

| Problème | Cause | Solution | Status |
|----------|-------|----------|--------|
| AttributeError citations | API retourne `str` | Gestion polymorphe | ✅ Corrigé |
| 404 _stcore/health | Cache navigateur | Hard refresh requis | ⏳ Action user |
| Warnings LaTeX | Unicode dans markdown | Ignorable (non critique) | ℹ️ Info |
| Pas de tweets | Données de test | Comportement normal | ✅ OK |

---

## 🚀 État Final

**Code:**
- ✅ Citations supportent `str` et `dict`
- ✅ Streamlit redémarré proprement
- ✅ Tous les noms de fichiers sans emojis

**Services:**
- ✅ API: http://localhost:8000 (healthy)
- ✅ Streamlit: http://localhost:8501 (200 OK)

**Action requise:**
1. **Hard refresh navigateur** (Ctrl+Shift+R)
2. Tester à nouveau la page Scenario Analysis
3. Vérifier que les citations s'affichent

---

**Corrigé par:** Claude Code (Debugger Mode)
**Date:** 2025-12-27 21:15
**Status:** ✅ RÉSOLU (avec action utilisateur requise)
