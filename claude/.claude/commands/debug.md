description: Debug complet du SaaS ResidConnect - vérifie config, fichiers, API, Airtable
allowed-tools: [Read, Write, Bash, Grep, Glob]
argument-hint: <section à déboguer> (optional: all, config, files, api, airtable)
model: sonnet

# DEBUG COMMAND - ResidConnect SaaS

## Vue d'ensemble
Cette commande diagnostique les problèmes du SaaS :
- Configuration (.env.local, package.json)
- Structure fichiers (présence fichiers critiques)
- Routes API (existence et syntaxe)
- Intégration Airtable (token, base ID, tables)
- État du projet (erreurs, warnings)

## Sections disponibles
- `all` (défaut) : Diagnostic complet
- `config` : Variables d'env, package.json, dépendances
- `files` : Structure fichiers, fichiers manquants
- `api` : Routes API, endpoints, syntaxe
- `airtable` : Token, base ID, tables, field IDs
- `errors` : Erreurs récentes, warnings

---

# PHASE 1: EXPLORATION

## Step 1: Vérifier les fichiers critiques

Read(.env.local)
  → Affiche les variables AIRTABLE_API_TOKEN, AIRTABLE_BASE_ID, etc.
  → Vérifie qu'elles ne sont pas vides
  → ⚠️ Flags si token commence pas par "pat"

Read(package.json)
  → Affiche scripts disponibles (dev, build, start)
  → Vérifie dépendances: next, react, typescript, bcryptjs
  → Affiche versions

Glob(app/api/**/route.ts)
  → Liste toutes les routes API créées
  → Affiche structure

Glob(app/*/page.tsx)
  → Liste toutes les pages créées
  → Vérifie tenant/, professional/, agency/

Glob(components/*.tsx)
  → Liste tous les components créés

Read(lib/types.ts)
  → Affiche les types TypeScript définis
  
Read(lib/airtable.ts)
  → Affiche la config Airtable (base ID, table IDs)
  → Vérifie les imports

Read(CLAUDE.md)
  → Affiche section "AIRTABLE SCHEMA REFERENCE"
  → Vérifie que table IDs correspondent à .env

---

# PHASE 2: VALIDATION

## Step 2A: Vérifier la configuration

✅ Check .env.local
  - AIRTABLE_API_TOKEN présent ? (commence par "pat")
  - AIRTABLE_BASE_ID présent ? (commence par "app")
  - NEXT_PUBLIC_API_URL défini ?
  - Aucune variable vide ?

✅ Check package.json
  - Script "dev" présent ?
  - Dependencies: next, react, typescript OK ?
  - DevDependencies: react-dom, typescript OK ?
  - bcryptjs installé ? (obligatoire pour auth)
  - Tailwind installé ? (si CSS avec Tailwind)

✅ Check tsconfig.json
  - Strict mode activé ? (strict: true)
  - Paths configurés ? (@/*)

## Step 2B: Vérifier la structure fichiers

✅ Fichiers critiques présents ?
  - ✓ .env.local
  - ✓ lib/types.ts
  - ✓ lib/airtable.ts
  - ✓ lib/auth.ts
  - ✓ app/api/auth/login/route.ts
  - ✓ app/api/auth/register/route.ts
  - ✓ app/api/tenant/tickets/route.ts
  - ✓ app/tenant/layout.tsx
  - ✓ app/tenant/dashboard/page.tsx
  - ✓ components/Navbar.tsx
  - ✓ components/TicketForm.tsx

✅ Fichiers manquants ?
  - Lister les fichiers attendus mais absents

## Step 2C: Vérifier Airtable

✅ Token valide ?
  - Format: commence par "pat" ?
  - Longueur: >40 caractères ?

✅ Base ID correct ?
  - Format: commence par "app" ?
  - Correspond à appmujqM67OAxGBby ?

✅ Table IDs corrects ?
  - RESIDENCES: tblx32X9SAlBpeB3C ?
  - TENANTS: tbl18r4MzBthXlnth ?
  - PROFESSIONALS: tblIcANCLun1lb2Ap ?
  - TICKETS: tbl2qQrpJc4PC9yfk ?

✅ Field IDs correspondent ?
  - Pour TENANTS: email (fldg4xlUQGWAMa1vq), password_hash, etc. ?
  - Pour TICKETS: title, description, status, etc. ?

---

# PHASE 3: DIAGNOSE

## Step 3: Identifier les problèmes

### Section CONFIG
Bash(npm list bcryptjs)
  → Affiche si bcryptjs est installé

Bash(npm list next)
  → Affiche version de Next.js

### Section FILES
Read(app/api/auth/login/route.ts)
  → Vérifie que la route existe
  → Affiche les imports
  → Vérifie qu'elle appelle Airtable

Read(app/tenant/dashboard/page.tsx)
  → Vérifie que la page existe
  → Affiche la structure

### Section API
Grep(app/api/**/route.ts, "export async function")
  → Liste toutes les méthodes HTTP définies

### Section AIRTABLE
Read(lib/airtable.ts)
  → Vérifie la fonction de connexion Airtable
  → Affiche comment les table IDs sont utilisés
  → Vérifie le Bearer token dans les headers

---

# PHASE 4: RAPPORT FINAL

## Output Summary

Affiche un rapport structuré :

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 DEBUG REPORT - ResidConnect SaaS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 CONFIGURATION
  ✅ .env.local présent
  ✅ AIRTABLE_API_TOKEN: pat... (valide)
  ✅ AIRTABLE_BASE_ID: appmujqM67OAxGBby
  ✅ bcryptjs installé v2.4.3
  ❌ Tailwind NOT installed (optional)

📁 STRUCTURE FICHIERS
  ✅ lib/types.ts
  ✅ lib/airtable.ts
  ✅ app/api/auth/login/route.ts
  ✅ app/tenant/dashboard/page.tsx
  ❌ app/agency/dashboard/page.tsx (manquant - pas critique)

🛣️ API ROUTES
  ✅ POST /api/auth/login
  ✅ POST /api/auth/register
  ✅ GET /api/tenant/tickets
  ✅ PATCH /api/tenant/tickets/[id]
  ✅ GET /api/professional/tickets

🗄️ AIRTABLE CONFIG
  ✅ Base ID: appmujqM67OAxGBby
  ✅ TENANTS Table: tbl18r4MzBthXlnth
  ✅ TICKETS Table: tbl2qQrpJc4PC9yfk
  ✅ PROFESSIONALS Table: tblIcANCLun1lb2Ap
  ⚠️ Field IDs: vérifier que fldg4xlUQGWAMa1vq existe

⚠️ AVERTISSEMENTS
  - Aucun warning détecté

❌ ERREURS
  - Aucune erreur détectée

✅ STATUS: READY TO RUN
   → npm run dev (port 3000)
   → Accès à http://localhost:3000/login

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Recommandations

Si erreurs trouvées :
1. ✅ Config: Vérifier .env.local et package.json
2. ✅ Fichiers: Créer les fichiers manquants
3. ✅ API: Vérifier la syntaxe des routes
4. ✅ Airtable: Vérifier token et table IDs

Si tout OK :
→ Lancer `npm run dev`
→ Accéder à http://localhost:3000/login
→ Tester login avec marie.dupont@mail.com / 123456

---

# UTILISATION

Appeler depuis Claude Code:
```
@debug all
@debug config
@debug airtable
```