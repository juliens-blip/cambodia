---
description: Réparation automatique d'un serveur MCP avec corrections guidées
allowed-tools: [Task]
argument-hint: <nom-du-mcp>
model: sonnet
---

# Réparation Automatique MCP

Vous devez réparer automatiquement un serveur MCP en utilisant l'agent **mcp-doctor**.

**MCP à réparer:** $ARGUMENTS

## Instructions

Lancez l'agent **mcp-doctor** avec le Task tool en mode réparation automatique:

```
MISSION: Réparer automatiquement le serveur MCP "$ARGUMENTS"

MODE: Réparation automatique avec validation minimale

PROCESSUS ACCÉLÉRÉ:

1. DIAGNOSTIC RAPIDE (1 min)
   - Lister MCPs: `claude mcp list`
   - Identifier status du MCP "$ARGUMENTS"
   - Lire configuration et fichiers critiques

2. DÉTECTION PROBLÈMES COMMUNS (1 min)
   - Chemins relatifs → absolus
   - Dépendances manquantes
   - Variables d'environnement absentes
   - Erreurs de syntaxe JSON

3. RÉPARATIONS AUTOMATIQUES (2-5 min)
   - Corriger claude_desktop_config.json automatiquement
   - Installer dépendances manquantes (pip install, npm install)
   - Créer .env depuis .env.example si absent
   - Corriger chemins avec conventions OS

4. VALIDATION (30s)
   - Tester `claude mcp list`
   - Vérifier status = Connected
   - Tester 1-2 handlers simples

5. RAPPORT CONCIS
   ✅ Corrections appliquées
   ⚠️  Warnings restants
   ❌ Problèmes nécessitant intervention manuelle

RÈGLES:
- Appliquer corrections sans demander confirmation pour:
  * Chemins relatifs → absolus
  * Installation dépendances standard
  * Corrections JSON syntax
  * Création .env depuis template

- DEMANDER confirmation pour:
  * Modifications du code métier
  * Suppressions de fichiers
  * Changements de versions majeures
  * Modifications de logique handlers

IMPORTANT: Si problèmes nécessitent intervention humaine, utiliser /mcp-check pour diagnostic détaillé.
```

Lance l'agent mcp-doctor en mode fix maintenant.
