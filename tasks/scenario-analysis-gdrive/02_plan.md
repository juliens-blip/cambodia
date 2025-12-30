# Plan d'Implementation: scenario-analysis-gdrive

## Informations
**Date:** 2025-12-30  
**Base sur:** tasks/scenario-analysis-gdrive/01_analysis.md  
**Approche:** Injecter le contexte GDrive dans l'endpoint /trends/scenario, en reutilisant les resultats de recherche deja obtenus par l'UI. Stabiliser l'indexation via l'admin v2 et corriger le script d'indexation local.

## Objectif final
Les analyses Scenario (pessimistic/realistic/optimistic) utilisent des extraits des documents Google Drive (GDrive) en plus des prix et tweets, avec une indexation stable et verifiable.

## Gap Analysis
| Etat actuel | Etat cible | Action requise |
| --- | --- | --- |
| UI fetch docs mais ne les envoie pas | L'API scenario recoit un contexte docs | Ajouter docs_context dans la requete scenario |
| API scenario ignore docs | Prompt inclut contexte GDrive | Modifier app/api/routes/trends.py |
| Indexation fragile (OOM) | Indexation stable | Basculer vers admin_v2 |
| Script local cassé | Script fonctionne | Remplacer embed_document par embed_text |
| Docs dimension 1024 vs 384 | Docs coherentes | Mettre a jour README/USER_GUIDE si necessaire |

## Architecture proposee
```
UI Scenario Analysis
  -> /api/v1/search (semantic search) -> docs_data
  -> build docs_context from docs_data
  -> /api/v1/trends/scenario (price + twitter + docs_context)
       -> Perplexity prompt inclut LOCAL DOCS
```

## Checklist technique (step-by-step)

### Phase 1: Preparation
- [x] **1.1** Identifier le format de docs_context
  - Action: definir un format unique (Source + Similarity + chunk_text)
  - Validation: docs_context max 5 chunks, taille raisonnable (<12k chars)

- [x] **1.2** Ajouter un helper UI pour construire docs_context
  - Fichier: `ui/pages/6_Scenario_Analysis.py`
  - Action: construire une string a partir de docs_data["results"]
  - Validation: docs_context vide si aucun resultat

- [x] **1.3** Etendre la requete scenario pour inclure docs_context
  - Fichier: `ui/pages/6_Scenario_Analysis.py`
  - Action: inclure docs_context dans le JSON envoye a /trends/scenario
  - Validation: payload contient price_data + twitter_data + docs_context

### Phase 2: API Scenario (docs in prompt)
- [x] **2.1** Accepter docs_context dans l'endpoint scenario
  - Fichier: `app/api/routes/trends.py`
  - Action: ajouter param body `docs_context: Optional[str]`
  - Validation: endpoint accepte les anciennes requetes (backward compatible)

- [x] **2.2** Injecter docs_context dans le prompt
  - Fichier: `app/api/routes/trends.py`
  - Action: construire un prompt qui commence par "LOCAL DOCUMENTS" si docs_context present
  - Validation: prompt utilise les docs si non vides, sinon fallback prompt actuel

- [x] **2.3** Retourner un statut docs_used
  - Fichier: `app/api/routes/trends.py`
  - Action: reponse inclut docs_used + docs_count (derive de docs_context)
  - Validation: UI peut afficher le statut si besoin

### Phase 3: Stabiliser l'indexation (Railway)
- [x] **3.1** Basculer vers admin_v2
  - Fichier: `app/main.py`
  - Action: remplacer import admin par admin_v2 (alias admin)
  - Validation: routes /api/v1/admin/* inchangées

- [ ] **3.2** Verifier indexation via Admin UI
  - Action: lancer "Start Indexation" et surveiller /indexation-status
  - Validation: chunks_indexed > 0, pas de crash OOM

### Phase 4: Fix script local (optionnel mais utile)
- [x] **4.1** Corriger scripts/index_existing_documents.py
  - Action: remplacer embed_document par embed_text
  - Validation: script demarre sans AttributeError

### Phase 5: Documentation (leger)
- [x] **5.1** Ajouter note 384D dans docs/phase3-semantic-search/README.md
  - Action: indiquer que le modele par defaut est e5-small (384D) en prod
  - Validation: doc alignee avec code actuel

## Commandes a executer (si besoin)
```bash
# Lancer l'indexation via l'UI admin (Railway)
# Verification rapide via API admin
curl -s $API_BASE_URL/api/v1/admin/indexation-status
```

## Risques identifies
| Risque | Impact | Mitigation |
| --- | --- | --- |
| docs_context trop long | Reponse Perplexity lente | Limiter top_k a 5 et tronquer chunks |
| embeddings encore vides | Aucun doc dans contexte | Valider indexation avant tests |
| duplication de recherche | Surcout temps | Reutiliser docs_data UI (pas de recherche serveur) |

## Points de validation
- [ ] /api/v1/admin/indexation-status -> chunks_indexed > 0
- [ ] UI Scenario Analysis affiche >0 docs analyzes
- [ ] Prompt scenario inclut LOCAL DOCUMENTS (logs ou debug)
- [ ] Aucune regression sur tweets/prix

## Estimation
- **Complexite:** Moyenne
- **Fichiers modifies:** 3-5
- **Fichiers crees:** 0
- **Dependances:** Aucune nouvelle

## Pret pour implementation
- [x] Analyse complete (01_analysis.md ok)
- [x] Plan valide par l'utilisateur
