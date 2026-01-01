# Analyse: Market Trends - Streamlit _stcore routing + CSX index null

## Contexte
**Date:** 2026-01-01 00:50
**Demande initiale:** Corriger le CSX Index (N/A) et l'auto-refresh Streamlit (erreurs /_stcore/health 404 + page qui boucle) sur Market Trends en production.
**Contexte additionnel:** Apres redeploy, erreur front React #321 (invalid hook call) sur index.js, auto-refresh toujours instable.
**Objectif:** Stabiliser la connexion Streamlit (auto-refresh OK, page non bloquee), eliminer l erreur React, et clarifier/fixer l'affichage CSX Index si possible.
**MAJ 2026-01-01:** Erreur "Connection refused" cote UI (API 127.0.0.1:8000), logs Railway montrent le health monitor qui tue l'API (health check fail 3x) avant que le port soit ouvert.

## Etat Actuel de la Codebase

### Fichiers Concernes
| Fichier | Type | Role | Lignes |
|---|---|---|---|
| start.py | Runtime | Lance FastAPI + Streamlit (pas de baseUrlPath) | L235-L265 |
| ui/pages/5_Market_Trends.py | UI | Auto-refresh + Macro indicators + fetch CSX index | L40-L255 |
| ui/pages/6_Scenario_Analysis.py | UI | Macro indicators + fetch CSX index | L237-L708 |
| ui/config.py | Config | API_BASE_URL pour l'UI | L1-L20 |
| C:\Users\beatr\AppData\Roaming\Python\Python314\site-packages\streamlit\static\static\js\index.3bHSf9gi.js | Vendor | getPossibleBaseUris() pour _stcore | ~L143 |

### Architecture Actuelle
`
[Browser] --(Streamlit UI on PORT)--> [Streamlit server]
   |                                   |_ static index.html (pas de BACKEND_BASE_URL)
   |                                   |_ _stcore endpoints (root)
   |
   |--(API calls)-> [FastAPI on 8000]
`

### Code Snippets Cles
#### start.py (lancement Streamlit)
`python
subprocess.run([
    sys.executable, "-m", "streamlit", "run",
    "ui/streamlit_app.py",
    "--server.port", port,
    "--server.address", "0.0.0.0",
    "--server.headless", "true",
    "--browser.gatherUsageStats", "false"
], check=True)
`

#### streamlit JS (base URI)
`javascript
function getPossibleBaseUris(){
  const n=parseUriIntoBaseParts(window.__streamlit?.BACKEND_BASE_URL);
  const {pathname:o}=n;
  if(o==="/") return [n];
  const e=o.split("/"), t=[];
  for(;e.length>0;){
    const c=new URL(n);
    c.pathname=e.join("/");
    t.push(c);
    e.pop();
  }
  return t.length<=2 ? t : t.slice(0,2);
}
`

#### ui/pages/5_Market_Trends.py (CSX index)
`python
@st.cache_data(ttl=900)
def fetch_csx_index():
    data = fetch_mef_json("csx-index")
    return data.get("data") if data else None
`

#### ui/pages/5_Market_Trends.py (auto-refresh)
`python
auto_refresh = st.sidebar.checkbox("Auto-refresh (60s)", value=False)
if auto_refresh:
    # Version production: sleep + rerun -> bloque le rendu et boucle
    time.sleep(60)
    st.rerun()
`

#### Console navigateur (React error 321)
`text
Minified React error #321 (Invalid hook call)
`

## Documentation Externe (Context7)
- **Context7:** indisponible dans ce runtime (MCP non charge). Fallback sur le code source Streamlit local (site-packages).
- **React error decoder (react.dev/errors/321):** Invalid hook call. Causes possibles: mismatch React/renderer, hooks hors composant, ou plusieurs copies de React.
- **Streamlit st.fragment (docstring locale):** permet un rerun periodique via `run_every` sans bloquer le rendu.

## Dependances

### Internes
- start.py -> lance ui/streamlit_app.py
- ui/pages/5_Market_Trends.py et ui/pages/6_Scenario_Analysis.py -> fetch_mef_json() pour MEF

### Externes
- Streamlit (v1.52.2): routing _stcore et front-end base URI
- httpx: appels MEF

## Points d'Attention
- **_stcore 404:** la JS Streamlit derive base URI depuis window.location sur /Market_Trends et tente /Market_Trends/_stcore/* alors que le serveur expose /_stcore/* (baseUrlPath vide).
- **Injection tardive:** BACKEND_BASE_URL est injecte en fin de `<head>`; si le module JS le lit avant, la variable reste undefined et _stcore continue sous /Market_Trends.
- **CSX index null:** l'endpoint MEF csx-index renvoie des champs value/change_percent a null (donnees upstream).
- **CSX index sans historique:** l'endpoint MEF renvoie une seule ligne, aucun parametre ne retourne d'historique.
- **Context7:** non disponible; aucune doc externe chargee automatiquement.
- **Auto-refresh bloque:** l'auto-refresh est execute en haut de page (sleep + rerun), ce qui empeche le rendu complet et donne l'impression de chargement en boucle.
- **Fallback CSX fragile:** la fallback via session_state saute apres un reload navigateur (nouvelle session), donc N/A persiste si la source reste null.
- **React #321:** erreur invalid hook call cote client, possiblement declenchee par un widget/custom component d auto-refresh.
- **API instable:** le health monitor termine l'API apres 3 checks fails, avant que le port soit ouvert (connection refused cote UI).
- **Cache-bust query:** le JS est charge avec `?v=codex-baseurl-1`; risque de duplication d'instance React si une autre page charge le bundle sans query (hypothese a verifier).

## Opportunites Identifiees
- Injecter window.__streamlit.BACKEND_BASE_URL = window.location.origin + '/' dans index.html avant le bundle JS pour forcer l'usage de /_stcore/*.
- Repositionner l'injection BACKEND_BASE_URL avant le script module (garantir la lecture).
- Ajouter un fallback "dernier index valide" (session/local) ou message explicite "source MEF renvoie null".
- Ajouter un override simple via env (CSX_INDEX_FALLBACK_VALUE + UPDATED_AT) pour afficher une valeur meme si MEF renvoie null.
- Remplacer l'auto-refresh bloquant par un refresh HTML (meta refresh) pour laisser le rendu s'afficher.
- Conserver un "dernier index valide" partage entre sessions (cache_resource ou variable globale) pour rester constant meme apres reload.
- Utiliser un refresh HTML sans widget pour eviter l erreur React.
- Ajouter un "grace period" au health monitor (ne pas tuer l'API avant readiness).
- Option: retirer le cache-bust query si l'erreur React persiste.
- Persistant CSX index: stocker la derniere valeur valide dans un fichier local (logs) pour survivre aux reloads.

## Resume Executif
- L'auto-refresh casse car Streamlit tente _stcore sous /Market_Trends, route inexistante quand server.baseUrlPath est vide.
- Le CSX Index est N/A car l'API MEF renvoie des valeurs nulles (probleme upstream, pas parsing).
- Le loop de chargement vient d'un auto-refresh bloquant (sleep + rerun) execute avant le rendu de la page.
- L erreur React #321 indique un invalid hook call, possiblement lie a l auto-refresh JS.
- Correctifs principaux: forcer le BACKEND_BASE_URL dans le HTML Streamlit, remplacer l'auto-refresh par meta refresh (sans widget), et garder un cache persistant pour le CSX index.
- Nouveau: l'API est instable car le health monitor la termine trop tot (connection refused).


