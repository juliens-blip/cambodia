# Guide d'Utilisation: APEX WORKFLOW (v2026)

## 🎯 Vue d'Ensemble

Le workflow APEX est un système de gestion de tâches complexes qui décompose chaque feature en 3 phases bien définies: **Analyze**, **Plan**, **Implement**. Chaque phase produit des artifacts persistés sur le disque pour une traçabilité complète.

## 🔗 Origine

Ce workflow est inspiré de la vidéo YouTube: [https://www.youtube.com/watch?v=jleAOlZn-tc](https://www.youtube.com/watch?v=jleAOlZn-tc)

**Stack utilisée:**
- Sub-agents spécialisés (Explore, Plan)
- Context7 MCP pour documentation à jour
- Persistance complète dans `tasks/`
- Validation utilisateur obligatoire

## 📚 Concepts Clés

### 1. Workflow en 3 Étapes

#### Étape 1: ANALYZE
- **Sub-agent:** Explore (modèle Haiku)
- **Objectif:** Comprendre l'état actuel de la codebase
- **Outils:** Grep, Glob, Read, Context7
- **Sortie:** `01_analysis.md`

**Pourquoi Haiku ?** Rapidité d'exécution pour les tâches d'exploration.

#### Étape 2: PLAN
- **Sub-agent:** Plan (modèle Sonnet/Opus)
- **Objectif:** Concevoir la stratégie d'implémentation
- **Outils:** Analyse du fichier `01_analysis.md`, Context7 pour best practices
- **Sortie:** `02_plan.md`
- **⚠️ POINT D'ARRÊT:** Validation utilisateur obligatoire

**Pourquoi Sonnet/Opus ?** Capacité de raisonnement complexe pour la planification stratégique.

#### Étape 3: IMPLEMENT
- **Mode:** Edit Automatically
- **Objectif:** Exécuter le plan validé
- **Référence:** `02_plan.md` (suivi strict)
- **Sortie:** `03_implementation_log.md`

### 2. Persistance sur Disque

**Problème résolu:** Perte de contexte entre sessions, décisions non documentées

**Solution:** Tous les artifacts sont sauvegardés dans `tasks/<feature>/`

**Avantages:**
- Reprise facile après interruption
- Traçabilité des décisions
- Collaboration facilitée
- Documentation automatique

### 3. Context7 Integration

**Problème résolu:** Documentation obsolète, syntaxe incorrecte des librairies

**Solution:** Consultation systématique de Context7 pour toutes les dépendances externes

**Workflow:**
```
1. Identifier librairie (ex: "next.js")
2. Résoudre ID: mcp__context7__resolve-library-id("next.js")
3. Récupérer docs: mcp__context7__get-library-docs("/vercel/next.js", topic="routing")
4. Documenter dans 01_analysis.md
```

### 4. Validation Utilisateur

**Problème résolu:** Implémentation incorrecte, rework coûteux

**Solution:** Validation obligatoire du plan avant implémentation

**Process:**
```
/plan <feature>
→ Agent produit 02_plan.md
→ AskUserQuestion("Le plan vous convient-il ?")
→ ATTENDRE validation
→ Si OK → /implement
→ Si NON → Ajuster plan
```

## 🚀 Guide Pratique

### Cas d'Usage 1: Feature Simple

**Demande utilisateur:**
```
Ajoute un bouton de logout dans le header
```

**Process complet:**

1. **Agent lance automatiquement /analyze**
   ```
   Création de tasks/logout-button/
   Lancement sub-agent Explore (haiku)
   → Trouve Header.tsx, auth.ts
   → Consulte Context7 pour React best practices
   → Produit 01_analysis.md
   ```

2. **Agent lance /plan**
   ```
   Lecture de 01_analysis.md
   Lancement sub-agent Plan (sonnet)
   → Crée checklist en 3 phases
   → Produit 02_plan.md
   → DEMANDE VALIDATION
   ```

3. **Utilisateur valide → Agent lance /implement**
   ```
   Initialise 03_implementation_log.md
   → Phase 1: Modifie Header.tsx
   → Phase 2: Implémente handleLogout()
   → Phase 3: Tests
   → Finalise le journal
   ```

**Temps total:** ~5-10 minutes (vs 30+ minutes sans workflow)

### Cas d'Usage 2: Feature Complexe

**Demande utilisateur:**
```
Implémente un système de cache Redis pour les API calls
```

**Process complet:**

1. **/analyze api-redis-cache**
   - Identifie 12 endpoints API existants
   - Consulte Context7 pour:
     * Redis documentation
     * ioredis library
     * Next.js caching strategies
   - Produit analyse complète (15 fichiers identifiés)

2. **/plan api-redis-cache**
   - Plan en 6 phases:
     1. Setup Redis (docker-compose)
     2. Middleware de cache
     3. Cache utils
     4. Intégration dans API routes
     5. Cache invalidation
     6. Tests & monitoring
   - Suggestion de parallélisation (optionnel)
   - DEMANDE VALIDATION

3. **/implement api-redis-cache**
   - Exécution séquentielle des 6 phases
   - Validation entre chaque phase
   - Mise à jour du journal en temps réel

**Temps total:** ~45-60 minutes (vs 3-4 heures sans workflow)

## 🎛️ Commandes Détaillées

### `/analyze <feature>`

**Syntaxe:**
```bash
/analyze <nom-de-la-feature>
```

**Exemples:**
```bash
/analyze user-authentication
/analyze payment-integration
/analyze dark-mode-toggle
```

**Ce qui se passe:**
1. Création de `tasks/<feature>/`
2. Lancement sub-agent Explore avec:
   - Grep/Glob pour trouver fichiers pertinents
   - Read pour extraire le code
   - Context7 pour documentation externe
3. Production de `01_analysis.md`

**Sortie:**
```
✅ Analyse terminée !
Fichier: tasks/<feature>/01_analysis.md

Résumé:
- X fichiers identifiés
- Y dépendances externes
- Z points d'attention

Voulez-vous que je procède au plan (/plan) ?
```

### `/plan <feature>`

**Syntaxe:**
```bash
/plan <nom-de-la-feature>
```

**Prérequis:** `01_analysis.md` doit exister

**Ce qui se passe:**
1. Lecture de `01_analysis.md`
2. Lancement sub-agent Plan avec:
   - Analyse du gap entre état actuel et objectif
   - Conception de l'architecture
   - Création de la checklist technique
   - Identification des risques
3. Production de `02_plan.md`
4. **DEMANDE VALIDATION** (AskUserQuestion)

**Sortie:**
```
✅ Plan créé !
Fichier: tasks/<feature>/02_plan.md

Phases:
- Phase 1: Préparation (3 items)
- Phase 2: Implémentation (5 items)
- Phase 3: Tests (2 items)

🛑 VALIDATION REQUISE
Le plan vous convient-il ?
[Options: Oui / Non / Ajustements nécessaires]
```

### `/implement <feature>`

**Syntaxe:**
```bash
/implement <nom-de-la-feature>
```

**Prérequis:**
- `01_analysis.md` existe
- `02_plan.md` existe ET validé

**Ce qui se passe:**
1. Confirmation finale
2. Initialisation de `03_implementation_log.md`
3. Exécution step-by-step selon `02_plan.md`:
   - Mode "Edit Automatically"
   - Validation après chaque phase
   - Mise à jour du journal en temps réel
4. Finalisation et résumé

**Sortie:**
```
✅ Implémentation terminée !

Résumé:
- X fichiers modifiés
- Y fichiers créés
- Z commandes exécutées

Tests: ✓ Tous passent
Performance: <métrique si applicable>

Journal: tasks/<feature>/03_implementation_log.md
```

### `/status <feature>`

**Syntaxe:**
```bash
/status <nom-de-la-feature>
```

**Sortie:**
```
# Statut: <feature>

## 📊 Progression
- ✅ Analyse (01_analysis.md) - Complété le <date>
- ✅ Plan (02_plan.md) - Validé le <date>
- ⏳ Implémentation (03_implementation_log.md) - En cours

## 📈 Avancement Implémentation
Phase 1: ✅ Complété (4/4 items)
Phase 2: ⏳ En cours (2/5 items)
Phase 3: ⏸️ En attente
Phase 4: ⏸️ En attente

## 🎯 Prochaine Action
Continuer Phase 2, item 2.3: "<description>"

## ⚠️ Blocages
<Description si applicable, sinon "Aucun">
```

### `/list`

**Syntaxe:**
```bash
/list
```

**Sortie:**
```
# Tâches APEX en cours

| Feature | Analyse | Plan | Implem | Statut |
|---------|---------|------|--------|--------|
| user-auth | ✅ | ✅ | ⏳ 40% | En cours |
| api-cache | ✅ | ✅ | ⏸️ | En attente |
| dark-mode | ✅ | ❌ | ❌ | Plan requis |

Légende:
✅ Complété | ⏳ En cours | ⏸️ En attente | ❌ Non démarré
```

## 🛠️ Intégration avec Context7

### Pourquoi Context7 ?

**Problème:** Documentation obsolète, hallucinations sur la syntaxe des librairies

**Solution:** Context7 fournit la documentation à jour directement depuis les sources officielles

### Workflow Context7

**Étape 1: Résoudre le Library ID**

```javascript
// Dans 01_analysis.md, l'agent doit:
mcp__context7__resolve-library-id(libraryName: "next.js")

// Retourne:
{
  libraryId: "/vercel/next.js/v14.0.4",
  description: "The React Framework for Production",
  benchmark_score: 95
}
```

**Étape 2: Récupérer la Documentation**

```javascript
// Mode "code" pour API refs et exemples
mcp__context7__get-library-docs(
  context7CompatibleLibraryID: "/vercel/next.js/v14.0.4",
  topic: "app-router",
  mode: "code",
  page: 1
)

// Mode "info" pour concepts et architecture
mcp__context7__get-library-docs(
  context7CompatibleLibraryID: "/vercel/next.js/v14.0.4",
  topic: "routing-fundamentals",
  mode: "info",
  page: 1
)
```

**Étape 3: Documenter dans 01_analysis.md**

```markdown
## 📚 Documentation Externe (Context7)

### Next.js v14.0.4
**Library ID:** /vercel/next.js/v14.0.4

**App Router - Documentation consultée:**
- Les routes sont définies dans `app/` directory
- Utiliser `page.tsx` pour les pages
- `layout.tsx` pour les layouts partagés
- Server Components par défaut

**Code Example:**
\`\`\`typescript
// app/dashboard/page.tsx
export default function DashboardPage() {
  return <h1>Dashboard</h1>
}
\`\`\`

**Source:** Context7 - mode:code, topic:app-router
```

### Best Practices Context7

1. **Toujours résoudre le library ID d'abord**
   - Ne pas deviner le format
   - Utiliser `resolve-library-id`

2. **Choisir le bon mode**
   - `mode: "code"` → API refs, syntaxe, exemples
   - `mode: "info"` → Concepts, architecture, guides

3. **Paginer si nécessaire**
   - Si contexte insuffisant, essayer `page: 2, 3, 4...`

4. **Spécifier le topic**
   - Plus précis = meilleure documentation
   - Exemples: "hooks", "routing", "authentication"

5. **Documenter la source**
   - Noter le library ID, topic, et mode utilisés
   - Permet de re-consulter si besoin

## 🎓 Exemples Complets

### Exemple 1: Ajout d'une Feature React

**Demande:**
```
Ajoute un composant de recherche avec debouncing
```

**Workflow:**

1. **Analyze Phase**
   ```
   Agent crée tasks/search-component/
   Agent explore:
   - components/ pour voir les patterns existants
   - lib/ pour les hooks custom éventuels

   Agent consulte Context7:
   - resolve-library-id("react")
   - get-library-docs("/facebook/react", topic: "hooks", mode: "code")
   - get-library-docs("/facebook/react", topic: "useEffect", mode: "code")

   Produit 01_analysis.md:
   - Patterns existants identifiés
   - Documentation React hooks
   - Aucun debouncing actuellement
   ```

2. **Plan Phase**
   ```
   Agent lit 01_analysis.md
   Agent crée plan:

   Phase 1: Créer hook useDebounce
   - Fichier: lib/hooks/useDebounce.ts
   - Pattern: React custom hook

   Phase 2: Créer composant SearchInput
   - Fichier: components/SearchInput.tsx
   - Props: { onSearch, placeholder, debounceMs }
   - État: useState pour input value

   Phase 3: Intégrer dans page
   - Fichier: app/search/page.tsx
   - Utiliser SearchInput + useDebounce

   Produit 02_plan.md
   DEMANDE VALIDATION
   ```

3. **Implement Phase (après validation)**
   ```
   Agent initialise 03_implementation_log.md

   Phase 1:
   ✅ Créé lib/hooks/useDebounce.ts (15 lignes)

   Phase 2:
   ✅ Créé components/SearchInput.tsx (42 lignes)

   Phase 3:
   ✅ Modifié app/search/page.tsx (intégration)

   Tests:
   ✅ Debouncing fonctionne (500ms)
   ✅ Recherche se déclenche correctement

   Finalise journal
   ```

**Résultat:**
- 2 fichiers créés
- 1 fichier modifié
- Documentation complète dans tasks/search-component/
- Temps: ~8 minutes

### Exemple 2: Intégration API Externe

**Demande:**
```
Intègre Stripe pour les paiements
```

**Workflow:**

1. **Analyze Phase**
   ```
   Agent crée tasks/stripe-integration/

   Agent explore:
   - app/api/ pour voir la structure API
   - .env pour les variables existantes
   - package.json pour les dépendances

   Agent consulte Context7:
   - resolve-library-id("stripe")
   - get-library-docs("/stripe/stripe-node", topic: "checkout", mode: "code")
   - get-library-docs("/stripe/stripe-node", topic: "webhooks", mode: "code")

   Agent WebSearch:
   - "Next.js Stripe integration best practices 2025"
   - "Stripe webhook security"

   Produit 01_analysis.md:
   - Aucune intégration paiement actuelle
   - API routes existantes: 8 endpoints
   - Documentation Stripe consultée
   - Best practices identifiées
   ```

2. **Plan Phase**
   ```
   Agent crée plan en 7 phases:

   Phase 1: Setup Stripe
   - Installer @stripe/stripe-js, stripe
   - Créer STRIPE_SECRET_KEY dans .env
   - Init Stripe client

   Phase 2: API Checkout
   - Créer app/api/checkout/route.ts
   - Implémenter création session

   Phase 3: Webhook Handler
   - Créer app/api/webhooks/stripe/route.ts
   - Vérifier signature
   - Gérer événements

   Phase 4: Frontend Intégration
   - Créer components/CheckoutButton.tsx
   - Redirect vers Stripe Checkout

   Phase 5: Success/Cancel Pages
   - app/payment/success/page.tsx
   - app/payment/cancel/page.tsx

   Phase 6: Sécurité
   - Webhook secret validation
   - CORS configuration

   Phase 7: Tests
   - Test mode Stripe
   - Validation flow complet

   Produit 02_plan.md
   DEMANDE VALIDATION
   ```

3. **Implement Phase**
   ```
   Agent exécute les 7 phases:

   Phase 1: ✅
   - package.json updated
   - .env.example updated
   - lib/stripe.ts created

   Phase 2: ✅
   - app/api/checkout/route.ts created

   Phase 3: ✅
   - app/api/webhooks/stripe/route.ts created

   Phase 4: ✅
   - components/CheckoutButton.tsx created

   Phase 5: ✅
   - Success/Cancel pages created

   Phase 6: ✅
   - Security implemented

   Phase 7: ✅
   - Tests passent

   Finalise 03_implementation_log.md
   ```

**Résultat:**
- 6 fichiers créés
- 2 fichiers modifiés (.env.example, package.json)
- Intégration complète et sécurisée
- Temps: ~30 minutes (vs 2-3h manuellement)

## 🚀 Axes d'Amélioration Futurs

Basé sur les best practices et la vidéo source:

### 1. Validation Automatique
**Problème:** Validation manuelle peut manquer des erreurs

**Solution proposée:**
- Ajouter phase 4: `/validate <feature>`
- Exécuter automatiquement:
  * Linter (ESLint, Prettier)
  * Type checker (TypeScript)
  * Tests unitaires
  * Build test
- Produire `04_validation_report.md`

**Implémentation:**
```bash
# Après /implement
/validate <feature>

→ npm run lint
→ npm run type-check
→ npm run test
→ npm run build

→ Produit 04_validation_report.md avec résultats
```

### 2. Rollback Automatique
**Problème:** Pas de retour arrière facile si implémentation échoue

**Solution proposée:**
- Commande `/rollback <feature>`
- Créer backup avant /implement
- Restaurer depuis git ou filesystem backup

**Implémentation:**
```bash
# Avant /implement
git stash push -m "backup-<feature>"

# Si échec
/rollback <feature>
→ git stash pop
```

### 3. Métriques de Qualité
**Problème:** Pas de scoring de la qualité du code produit

**Solution proposée:**
- Intégrer SonarQube ou Code Climate
- Mesurer:
  * Complexité cyclomatique
  * Code coverage
  * Duplication
  * Maintenabilité
- Produire `05_quality_metrics.md`

### 4. Templates Personnalisés
**Problème:** Format fixe des fichiers .md

**Solution proposée:**
- Permettre templates custom dans `templates/`
- Exemples:
  * `templates/analysis-api.md`
  * `templates/plan-frontend.md`
  * `templates/analysis-backend.md`

**Usage:**
```bash
/analyze <feature> --template api
→ Utilise templates/analysis-api.md
```

### 5. Collaboration Multi-Agents
**Problème:** Un seul agent séquentiel

**Solution proposée:**
- Paralléliser les agents:
  * Agent A: Analyze (Explore)
  * Agent B: Prepare environment
  * Agent C: Review documentation
- Synchroniser via fichiers de statut
- Merge des résultats

### 6. Intégration CI/CD
**Problème:** Pas de déploiement automatique

**Solution proposée:**
- Après /implement, déclencher pipeline:
  * Build
  * Tests E2E
  * Deploy preview (Vercel, Netlify)
- Feedback dans `03_implementation_log.md`

## ✅ Checklist de Démarrage

Pour utiliser APEX WORKFLOW:

- [ ] Vérifier que l'agent `apex-workflow` existe dans `agents/`
- [ ] Vérifier que `tasks/` est initialisé
- [ ] Comprendre les 3 étapes: Analyze, Plan, Implement
- [ ] Comprendre la validation obligatoire après Plan
- [ ] Connaître les commandes: /analyze, /plan, /implement, /status, /list
- [ ] Comprendre l'utilisation de Context7
- [ ] Lire les règles d'or

## 📞 Support et Documentation

**Fichiers de référence:**
- `agents/apex-workflow.md` - Définition complète de l'agent
- `tasks/README.md` - Guide rapide du dossier tasks
- `docs/APEX_WORKFLOW_GUIDE.md` - Ce fichier (guide détaillé)

**Vidéo source:**
- [https://www.youtube.com/watch?v=jleAOlZn-tc](https://www.youtube.com/watch?v=jleAOlZn-tc)

**Documentation externe:**
- Claude Code: https://code.claude.com/docs
- Context7: Via MCP intégré
- Agent Skills: https://github.com/anthropics/skills

---

**Prêt à utiliser APEX WORKFLOW ? Commence par une tâche simple pour tester le workflow !**
