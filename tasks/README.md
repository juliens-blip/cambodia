# APEX FILE Tasks Directory (v2026)

Ce dossier contient toutes les tâches gérées par le workflow APEX orchestré par l'agent `apex-workflow`.

## 📁 Structure

Chaque feature/tâche a son propre sous-dossier organisé comme suit:

```
tasks/
├── README.md                     # Ce fichier
├── <nom-de-la-feature>/         # Un dossier par feature
│   ├── 01_analysis.md           # Résultats de /analyze
│   ├── 02_plan.md               # Résultats de /plan
│   ├── 03_implementation_log.md # Journal d'exécution
│   ├── assets/                  # Assets spécifiques (optionnel)
│   └── notes/                   # Notes complémentaires (optionnel)
```

## 🔄 Workflow APEX

### Étape 1: /analyze
**Objectif:** Explorer la codebase et la documentation pour comprendre l'état actuel

**Sortie:** `01_analysis.md` contenant:
- Fichiers concernés
- Architecture actuelle
- Documentation externe (Context7)
- Dépendances
- Points d'attention

### Étape 2: /plan
**Objectif:** Définir la stratégie d'implémentation step-by-step

**Sortie:** `02_plan.md` contenant:
- Gap analysis
- Architecture proposée
- Checklist technique détaillée
- Risques identifiés
- Points de validation

**⚠️ POINT D'ARRÊT:** Validation utilisateur requise avant de continuer.

### Étape 3: /implement
**Objectif:** Implémenter les modifications selon le plan validé

**Sortie:** `03_implementation_log.md` contenant:
- Progression en temps réel
- Problèmes rencontrés
- Modifications apportées
- Résultat final

## 🎛️ Commandes Disponibles

### `/analyze <feature>`
Lancer l'analyse d'une feature.

**Exemple:**
```
/analyze user-authentication
```

### `/plan <feature>`
Créer le plan d'implémentation (nécessite 01_analysis.md).

**Exemple:**
```
/plan user-authentication
```

### `/implement <feature>`
Exécuter le plan (nécessite plan validé).

**Exemple:**
```
/implement user-authentication
```

### `/status <feature>`
Afficher l'état d'avancement d'une feature.

**Exemple:**
```
/status user-authentication
```

### `/list`
Lister toutes les tâches en cours.

## ✅ Règles d'Or

1. **Ne JAMAIS coder avant analyse + plan**
2. **Toujours utiliser Context7 pour les dépendances externes**
3. **Demander validation avant /implement**
4. **Suivre STRICTEMENT le plan validé**
5. **Persister TOUT sur le disque**
6. **Un dossier = Une feature**

## 📊 Légende Statuts

- ✅ = Complété
- ⏳ = En cours
- ⏸️ = En attente
- ❌ = Non démarré

## 🚀 Démarrage Rapide

1. Créer une nouvelle tâche:
   ```
   /analyze ma-nouvelle-feature
   ```

2. Réviser l'analyse dans `tasks/ma-nouvelle-feature/01_analysis.md`

3. Créer le plan:
   ```
   /plan ma-nouvelle-feature
   ```

4. Réviser le plan dans `tasks/ma-nouvelle-feature/02_plan.md`

5. Valider le plan quand demandé

6. Exécuter:
   ```
   /implement ma-nouvelle-feature
   ```

7. Suivre la progression dans `tasks/ma-nouvelle-feature/03_implementation_log.md`

## 🎯 Avantages du Workflow APEX

- **Traçabilité complète:** Toutes les décisions documentées
- **Réduction des erreurs:** Plan validé avant implémentation
- **Contexte persistant:** Reprise facile après interruption
- **Documentation automatique:** Architecture et décisions capturées
- **Collaboration facilitée:** Fichiers partagés entre agents/humains

---

**Workflow APEX (v2026) - Documentation complète dans `agents/apex-workflow.md`**
