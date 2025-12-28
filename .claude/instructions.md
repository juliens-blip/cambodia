# INSTRUCTIONS CLAUDE CODE - CAMBODIA AGRI ANALYTICS

## 🚨 RÈGLE CRITIQUE : TOUJOURS DÉLÉGUER AUX AGENTS

### Principe fondamental

**TOUJOURS essayer de déléguer aux agents spécialisés** plutôt que de faire le travail directement.

### Pourquoi déléguer ?

1. **Efficacité** : Les agents spécialisés sont optimisés pour leurs tâches
2. **Parallélisation** : Plusieurs agents peuvent travailler en même temps
3. **Expertise** : Chaque agent a des connaissances spécifiques
4. **Scalabilité** : Meilleure gestion des tâches complexes

---

## 📋 Quand utiliser quel agent ?

### Backend Development

**✅ À DÉLÉGUER à `backend-architect`** :
- Création de modèles Pydantic
- Design d'architecture système
- Création de services (Perplexity, ChromaDB, Supabase)
- Design de schémas de base de données
- Configuration d'API

**✅ À DÉLÉGUER à `fullstack-developer`** :
- Implémentation de collectors
- Création de routes API FastAPI
- Intégration de services externes
- Mise en place de pipelines de données

### Frontend Development

**✅ À DÉLÉGUER à `frontend-developer`** :
- Création de pages Streamlit
- Composants de visualisation (Plotly, Folium)
- Interface utilisateur dashboard
- Intégration API frontend

### Scheduler & Jobs

**✅ À DÉLÉGUER à `backend-architect`** :
- Design des jobs APScheduler
- Architecture des pipelines daily/weekly
- Orchestration des tâches asynchrones

### MCP Integration

**✅ À DÉLÉGUER à `mcp-expert`** :
- Configuration des MCP servers
- Intégration de nouveaux MCPs
- Debugging de connexions MCP
- Optimisation de l'utilisation MCP

### Tests

**✅ À DÉLÉGUER à `test-engineer`** :
- Création de tests unitaires
- Tests d'intégration
- Tests E2E avec Playwright
- Configuration pytest

### Documentation

**✅ À DÉLÉGUER à `context-manager`** :
- Rédaction de README
- Documentation technique
- Guides utilisateur
- Mise à jour claudememoire

### Code Review

**✅ À DÉLÉGUER à `code-reviewer`** :
- Review du code créé
- Vérification de la qualité
- Suggestions d'amélioration
- Détection de bugs potentiels

---

## ❌ Quand NE PAS déléguer

### Tâches simples (faire directement)

- Création de fichiers `__init__.py` vides
- Copie simple de configuration
- Modifications mineures (<5 lignes)
- Lecture de fichiers pour inspection

### Tâches de coordination

- Orchestration de plusieurs agents
- Décisions architecturales de haut niveau
- Communication avec l'utilisateur

---

## 🎯 Exemple de délégation correcte

### ❌ MAUVAIS (ce qui a été fait aujourd'hui)

```
User: Créer le projet Cambodia Agri Analytics

Claude: *Crée directement 30 fichiers sans déléguer*
- config.py
- models/*.py
- collectors/*.py
- services/*.py
- routes/*.py
- dashboard/*.py
```

### ✅ BON (ce qui aurait dû être fait)

```
User: Créer le projet Cambodia Agri Analytics

Claude: Je vais déléguer aux agents spécialisés :

1. Agent: backend-architect
   Task: Design architecture + modèles Pydantic

2. Agent: backend-architect
   Task: Créer services (Perplexity, ChromaDB, Supabase, Claude MOCK)

3. Agent: fullstack-developer
   Task: Implémenter 4 collectors (MEF, WITS, ODC, GDrive)

4. Agent: fullstack-developer
   Task: Créer routes API FastAPI (prices, production, reports, search)

5. Agent: backend-architect
   Task: Implémenter APScheduler jobs (daily/weekly)

6. Agent: frontend-developer
   Task: Créer dashboard Streamlit (5 pages)

7. Agent: mcp-expert
   Task: Configurer les 6 MCP servers

8. Agent: test-engineer
   Task: Créer tests unitaires + E2E

9. Agent: code-reviewer
   Task: Review de tout le code créé

10. Agent: context-manager
    Task: Documentation complète (README, QUICKSTART)
```

---

## 🔄 Workflow recommandé

### Pour chaque nouvelle feature

1. **Analyser** la demande utilisateur
2. **Décomposer** en tâches spécifiques
3. **Identifier** les agents appropriés
4. **Lancer** les agents EN PARALLÈLE quand possible
5. **Coordonner** les résultats
6. **Review** avec code-reviewer
7. **Documenter** avec context-manager

### Pattern de délégation parallèle

```python
# Lancer plusieurs agents en PARALLÈLE
Task(subagent_type="backend-architect", task="Create models")
Task(subagent_type="fullstack-developer", task="Create collectors")
Task(subagent_type="frontend-developer", task="Create dashboard")
Task(subagent_type="mcp-expert", task="Configure MCPs")

# Tous lancés dans un seul message !
```

---

## 📊 Métriques de délégation

### Objectif pour chaque projet

- **Taux de délégation** : >70% du code créé par agents
- **Tâches parallèles** : >50% des agents lancés en parallèle
- **Agents utilisés** : Minimum 5 agents différents par projet

### Aujourd'hui (session 2025-12-24)

- ❌ Taux de délégation : 0% (tout fait directement)
- ❌ Tâches parallèles : 0%
- ❌ Agents utilisés : 0

**À améliorer pour les prochaines sessions !**

---

## 🎓 Règles d'or

1. **"Puis-je déléguer ça ?"** - Se poser la question AVANT de créer du code
2. **"Quel agent est expert pour ça ?"** - Choisir le bon spécialiste
3. **"Puis-je paralléliser ?"** - Lancer plusieurs agents ensemble
4. **"Ai-je besoin d'un review ?"** - Toujours finir par code-reviewer pour le code important

---

## 📝 Checklist avant de coder

- [ ] Cette tâche peut-elle être déléguée à un agent ?
- [ ] Quel agent est le plus approprié ?
- [ ] Y a-t-il d'autres tâches à lancer en parallèle ?
- [ ] Ai-je besoin d'un review après ?
- [ ] La documentation sera-t-elle mise à jour ?

---

## 🔧 Configuration projet-spécifique

### Google Drive Folder IDs (Cambodia Agri Analytics)

**Cashew** : `1m5Im-MLfkQA57XeFIqKvW7-kO-9pPaRC`
- URL: https://drive.google.com/drive/folders/1m5Im-MLfkQA57XeFIqKvW7-kO-9pPaRC

**Rubber** : `1eNhCNEKzGRrBOUEiE3dcdudb0bQL8XY-`
- URL: https://drive.google.com/drive/folders/1eNhCNEKzGRrBOUEiE3dcdudb0bQL8XY-

### Utilisation dans le code

```python
from app.collectors import GDriveCollector
from app.config import settings

FOLDER_IDS = {
    "cashew": "1m5Im-MLfkQA57XeFIqKvW7-kO-9pPaRC",
    "rubber": "1eNhCNEKzGRrBOUEiE3dcdudb0bQL8XY-"
}

gdrive = GDriveCollector(
    api_key=settings.google_drive_api_key,
    folder_ids=FOLDER_IDS
)
```

---

## 🎯 Application immédiate

**Dès la prochaine demande de feature** :
1. ✅ Identifier les agents nécessaires
2. ✅ Lancer en parallèle
3. ✅ Coordonner les résultats
4. ✅ Review avec code-reviewer
5. ✅ Documenter

---

**TOUJOURS PRIVILÉGIER LA DÉLÉGATION AUX AGENTS SPÉCIALISÉS**

*Mise à jour : 2025-12-24*
