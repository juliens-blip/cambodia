description: Auto-fix - répare automatiquement les problèmes détectés dans ResidConnect
allowed-tools: [Read, Write, Bash, Grep, Glob, Edit]
argument-hint: <section à réparer> (optional: all, config, imports, syntax, airtable)
model: sonnet

# AUTOFIX COMMAND - ResidConnect SaaS

## Vue d'ensemble
Cette commande détecte ET RÉPARE automatiquement les problèmes du SaaS :
- Fichiers manquants → Créer les fichiers
- Imports manquants → Ajouter les imports
- Variables d'env manquantes → Ajouter à .env.local
- Erreurs de syntaxe → Corriger le code
- Incohérences Airtable → Fixer les IDs
- Dépendances manquantes → npm install

⚠️ ATTENTION: Cette commande MODIFIE des fichiers. Vérifier après !

## Sections disponibles
- `all` (défaut) : Auto-fix complet
- `config` : Créer .env.local, package.json
- `imports` : Ajouter les imports manquants
- `syntax` : Corriger erreurs de syntaxe
- `airtable` : Fixer les IDs Airtable
- `dependencies` : Installer les packages

---

# PHASE 1: DIAGNOSTIQUE (RAPIDE)

## Step 1: Identifier les problèmes

### 1.1: Vérifier .env.local
Existe(.env.local) ?
  ❌ NON → Créer le fichier
  ✅ OUI → Vérifier les variables

### 1.2: Vérifier les fichiers critiques
Glob(app/api/**/route.ts)
  → Compter les fichiers
  → Si < 5 fichiers → créer les manquants

Glob(lib/*.ts)
  → Vérifier types.ts, airtable.ts, auth.ts

Glob(components/*.tsx)
  → Vérifier Navbar.tsx, TicketForm.tsx, TicketCard.tsx, DashboardCard.tsx

### 1.3: Vérifier les imports
Grep(app/**/*.tsx, "import.*Airtable")
  → Vérifier que les imports existent
  → Lister les imports manquants

### 1.4: Vérifier la syntaxe
Bash(npm run build 2>&1)
  → Capture les erreurs de build
  → Affiche les lignes problématiques

---

# PHASE 2: RÉPARATION AUTOMATIQUE

## Step 2A: Créer .env.local (s'il manque)

Write(.env.local)
```
# Airtable Configuration
AIRTABLE_API_TOKEN=your_airtable_token_here
AIRTABLE_BASE_ID=appmujqM67OAxGBby

# Airtable Table IDs
NEXT_PUBLIC_AIRTABLE_RESIDENCES=tblx32X9SAlBpeB3C
NEXT_PUBLIC_AIRTABLE_TENANTS=tbl18r4MzBthXlnth
NEXT_PUBLIC_AIRTABLE_PROFESSIONALS=tblIcANCLun1lb2Ap
NEXT_PUBLIC_AIRTABLE_TICKETS=tbl2qQrpJc4PC9yfk

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:3000/api

# Application
NODE_ENV=development
```

Output: ✅ .env.local créé

## Step 2B: Créer/Fixer lib/types.ts (s'il manque)

Write(lib/types.ts)
```typescript
// Types partagés pour ResidConnect SaaS

export type UserRole = 'tenant' | 'professional' | 'agency';

export interface User {
  id: string;
  email: string;
  role: UserRole;
  first_name?: string;
  last_name?: string;
  name?: string;
  unit?: string;
  phone?: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface Ticket {
  id: string;
  title: string;
  description: string;
  category: 'plomberie' | 'électricité' | 'concierge' | 'autre';
  status: 'open' | 'assigned' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  tenant_email: string;
  unit: string;
  assigned_to?: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  resolution_notes?: string;
  images_urls?: string;
}

export interface TicketFilters {
  status?: string;
  category?: string;
  priority?: string;
}

export interface AirtableRecord {
  id: string;
  fields: Record<string, any>;
}

export interface AirtableResponse {
  records: AirtableRecord[];
  offset?: string;
}
```

Output: ✅ lib/types.ts créé

## Step 2C: Créer/Fixer lib/airtable.ts (s'il manque)

Write(lib/airtable.ts)
```typescript
// Client Airtable centralisé

const BASE_ID = process.env.AIRTABLE_BASE_ID;
const API_TOKEN = process.env.AIRTABLE_API_TOKEN;
const API_URL = `https://api.airtable.com/v0/${BASE_ID}`;

// Table IDs
export const TABLES = {
  RESIDENCES: 'tblx32X9SAlBpeB3C',
  TENANTS: 'tbl18r4MzBthXlnth',
  PROFESSIONALS: 'tblIcANCLun1lb2Ap',
  TICKETS: 'tbl2qQrpJc4PC9yfk',
};

// Field IDs - TENANTS
export const TENANT_FIELDS = {
  email: 'fldg4xlUQGWAMa1vq',
  password_hash: 'fld1BkzQo0EqKUMVM',
  first_name: 'fldCjf3UHzuXYax8B',
  last_name: 'fldsGDRvealJ3yZdR',
  unit: 'fld9QHC92B3G3mEWn',
  phone: 'fldV1nK2VzfncFWIa',
  residence_name: 'fldEKoG8PUyQLCC37',
  status: 'fldK0XdnyBXTOkVfc',
  created_at: 'fldqd2KQ55XMKnF3R',
};

// Field IDs - TICKETS
export const TICKET_FIELDS = {
  title: 'fld51ebPXV9129Tof',
  description: 'fldSs15cz93JSy6zO',
  category: 'fldx8DUYFYylqMyq1',
  status: 'fldT3OYmpscavHWgC',
  priority: 'fldx5UszT8duxQZyY',
  tenant_email: 'fldZGRcdiXnoNS5OL',
  unit: 'fldRj1kcmJSu4nQQ2',
  assigned_to: 'fld3bfcdn71PUNPZI',
  created_at: 'fldDIUilSLOXpLuec',
  updated_at: 'fldwa2gEGI645x9FC',
  resolved_at: 'flddYiLBPnCYtBClV',
  resolution_notes: 'fldOWkLenvlefCm7Q',
  images_urls: 'flduOSxLcMx3dXktM',
};

// Field IDs - PROFESSIONALS
export const PROFESSIONAL_FIELDS = {
  email: 'fldqgHmvZ7OFLCiBb',
  password_hash: 'fldk8Bk0F35G8I8jx',
  name: 'fldLZ9GvZ3MvLNUyP',
  type: 'fldNbHwBSYIaUON0b',
  phone: 'fldRilhbZ3K92MnN8',
  agency_email: 'fldVubvDazWwArvo9',
  specialties: 'fldNNWbU6lWIfx4Gt',
  created_at: 'fldCZ6frTyuEBy0v3',
};

/**
 * Fetch depuis Airtable avec authentification
 */
export async function airtableFetch(
  endpoint: string,
  options: RequestInit = {}
) {
  const url = `${API_URL}/${endpoint}`;

  const headers: HeadersInit = {
    'Authorization': `Bearer ${API_TOKEN}`,
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Airtable API error: ${error.error?.message || response.statusText}`);
  }

  return response.json();
}

/**
 * Récupérer tous les records d'une table
 */
export async function getRecords(tableId: string, filterByFormula?: string) {
  let endpoint = `${tableId}`;
  
  if (filterByFormula) {
    endpoint += `?filterByFormula=${encodeURIComponent(filterByFormula)}`;
  }

  return airtableFetch(endpoint);
}

/**
 * Récupérer un record par ID
 */
export async function getRecord(tableId: string, recordId: string) {
  return airtableFetch(`${tableId}/${recordId}`);
}

/**
 * Créer un record
 */
export async function createRecord(tableId: string, fields: Record<string, any>) {
  return airtableFetch(tableId, {
    method: 'POST',
    body: JSON.stringify({ fields }),
  });
}

/**
 * Mettre à jour un record
 */
export async function updateRecord(
  tableId: string,
  recordId: string,
  fields: Record<string, any>
) {
  return airtableFetch(`${tableId}/${recordId}`, {
    method: 'PATCH',
    body: JSON.stringify({ fields }),
  });
}

/**
 * Supprimer un record
 */
export async function deleteRecord(tableId: string, recordId: string) {
  return airtableFetch(`${tableId}/${recordId}`, {
    method: 'DELETE',
  });
}
```

Output: ✅ lib/airtable.ts créé

## Step 2D: Créer/Fixer lib/auth.ts (s'il manque)

Write(lib/auth.ts)
```typescript
// Utilitaires d'authentification

import { User, AuthResponse } from './types';

const TOKEN_KEY = 'auth_token';
const USER_KEY = 'auth_user';

/**
 * Sauvegarder le token et user en localStorage
 */
export function saveAuth(token: string, user: User) {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

/**
 * Récupérer le token
 */
export function getToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(TOKEN_KEY);
  }
  return null;
}

/**
 * Récupérer l'utilisateur
 */
export function getUser(): User | null {
  if (typeof window !== 'undefined') {
    const user = localStorage.getItem(USER_KEY);
    return user ? JSON.parse(user) : null;
  }
  return null;
}

/**
 * Vérifier si l'utilisateur est authentifié
 */
export function isAuthenticated(): boolean {
  return !!getToken() && !!getUser();
}

/**
 * Vérifier le rôle de l'utilisateur
 */
export function hasRole(requiredRole: string): boolean {
  const user = getUser();
  return user?.role === requiredRole;
}

/**
 * Déconnecter
 */
export function logout() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
}
```

Output: ✅ lib/auth.ts créé

## Step 2E: Installer dépendances manquantes

Bash(npm install bcryptjs)
  → Si bcryptjs manque

Bash(npm install)
  → Réinstaller toutes les dépendances

Output: ✅ Dépendances installées

## Step 2F: Fixer les imports manquants dans fichiers existants

Read(app/api/auth/login/route.ts)
  → Si file existe, vérifier imports
  → Ajouter imports manquants (airtableFetch, etc.)

Read(app/tenant/dashboard/page.tsx)
  → Si file existe, vérifier imports
  → Ajouter imports manquants (User, useEffect, etc.)

Edit(...route.ts, ...page.tsx)
  → Ajouter les imports manquants en haut de fichier

Output: ✅ Imports corrigés

---

# PHASE 3: VALIDATION

## Step 3: Vérifier que tout est bon

Bash(npm run build 2>&1)
  → Capture les erreurs de build
  → Si erreurs → afficher et proposer solutions

Bash(npm run lint 2>&1)
  → Vérifier les erreurs TypeScript
  → Afficher les warnings/erreurs

---

# PHASE 4: RAPPORT FINAL

Affiche un rapport de ce qui a été réparé :

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 AUTOFIX REPORT - ResidConnect SaaS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ FICHIERS CRÉÉS
  ✅ .env.local
  ✅ lib/types.ts
  ✅ lib/airtable.ts
  ✅ lib/auth.ts

✅ IMPORTS CORRIGÉS
  ✅ app/api/auth/login/route.ts (4 imports ajoutés)
  ✅ app/tenant/dashboard/page.tsx (3 imports ajoutés)

✅ DÉPENDANCES INSTALLÉES
  ✅ bcryptjs@2.4.3
  ✅ Toutes les dépendances OK

✅ BUILD STATUS
  ✅ npm run build réussi (0 erreurs)

✅ LINT STATUS
  ✅ npm run lint réussi (0 warnings)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 PROCHAINES ÉTAPES
  1. npm run dev (lancer le serveur)
  2. Accéder à http://localhost:3000/login
  3. Tester le login avec marie.dupont@mail.com / 123456

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

# UTILISATION

Appeler depuis Claude Code:
```
@autofix all
@autofix config
@autofix imports
@autofix dependencies
```