# Plan d Implementation: scenario-doc-filtering

## Informations
**Date:** 2025-12-30  
**Base sur:** tasks/scenario-doc-filtering/01_analysis.md  
**Approche:** Ameliorer la selection en ajoutant un pipeline de mots-cles (tweets/news/market), puis filtrage qualite + ranking par document_id.

## Objectif final
Selectionner des documents essentiels (pertinents pour le contexte matieres premieres + tendances) et expliquer clairement pourquoi d autres ne sont pas retenus.

## Gap Analysis
| Etat actuel | Etat cible | Action requise |
| --- | --- | --- |
| Requete fixe | Requete enrichie (tweets/news/market) | Extraire keywords du contexte | 
| Top_k brut | Selection par doc_id + ranking | Regrouper + scorer + filtrer | 
| Aucun filtrage qualite | Exclure OCR bruit / titres generiques | Heuristiques de qualite | 
| Explication generique | Explication + stats selection | Afficher candidats/filtrés |

## Architecture proposee
```
Scenario UI
  -> extract_keywords(twitter_data, market_data)
  -> search_query = base + keywords
  -> /api/v1/search (top_k = candidats)
  -> select_documents(candidats)
      - dedup par document_id
      - filtre qualite (ratio lettres, taille)
      - score = similarite + bonus keywords
  -> docs_context (top N documents)
  -> UI: liste documents + raisons generales
```

## Checklist technique (step-by-step)

### Phase 1: Preparation
- [x] **1.1** Definir constantes de selection
  - Fichier: `ui/pages/6_Scenario_Analysis.py`
  - Ajouter: DOCS_CANDIDATES, DOCS_SELECTED, KEYWORDS_LIMIT

- [x] **1.2** Ajouter un extracteur de mots-cles
  - Fichier: `ui/pages/6_Scenario_Analysis.py`
  - Source: top_tweets, twitter_summary, news_summary, market_summary, key_factors, news_articles
  - Filtrage: stopwords, taille minimale

### Phase 2: Recherche enrichie
- [x] **2.1** Construire une requete enrichie
  - Base: "{commodity} market trends prices analysis"
  - Ajouter: keywords extraits (limite)

- [x] **2.2** Recuperer plus de candidats
  - top_k = DOCS_CANDIDATES (ex: 15)
  - threshold conserve (0.3)

### Phase 3: Selection intelligente
- [x] **3.1** Regrouper par document_id
  - Garder le chunk le plus similaire par document

- [x] **3.2** Filtre qualite (OCR bruit)
  - Exclure si ratio lettres < 0.25 ou nb mots < 40

- [x] **3.3** Scoring et ranking
  - score = similarity + bonus keywords + bonus domaine
  - penalites titres generiques (abbreviation, glossary, appendix, test)

- [x] **3.4** Selection finale
  - Garder top DOCS_SELECTED (ex: 5)

### Phase 4: Affichage + explication
- [x] **4.1** Utiliser la selection pour docs_context
- [x] **4.2** Mettre a jour la section "Documents utilises"
  - Afficher candidats vs selection
  - Raisons generales: top_k, seuil, filtres, qualite, dedup

### Phase 5: Memoire
- [x] **5.1** Documenter dans `claudememoire` et `MEMOIRE_CLAUDE.md`

## Points de validation
- [ ] Les docs selectionnes sont plus coherents avec tweets/tendances
- [ ] Les docs generiques (abbreviation/test) sont exclus
- [ ] L explication UI correspond au nouveau filtrage

## Estimation
- **Complexite:** Moyenne
- **Fichiers modifies:** 1-2
- **Fichiers crees:** 0
- **Dependances:** Aucune

## Pret pour implementation
- [x] Analyse complete (01_analysis.md ok)
- [x] Plan valide par l utilisateur
