---
description: Diagnostic et debugging complet d'un serveur MCP avec l'agent mcp-doctor
allowed-tools: [Task]
argument-hint: [nom-du-mcp] (optionnel)
model: sonnet
---

# Diagnostic MCP (MCP Doctor)

Vous devez diagnostiquer et debugger un serveur MCP en utilisant l'agent spécialisé **mcp-doctor**.

**Argument fourni:** $ARGUMENTS

## Instructions

Lancez l'agent **mcp-doctor** avec le Task tool en lui fournissant le prompt suivant:

```
Effectue un diagnostic complet du serveur MCP${ $ARGUMENTS ? " : " + $ARGUMENTS : "" }.

Suis le processus complet en 5 phases:

PHASE 1: DISCOVERY & TRIAGE
- Identifier le MCP à diagnostiquer${ !$ARGUMENTS ? " (demander à l'utilisateur si non fourni)" : "" }
- Lister tous les MCPs avec `claude mcp list`
- Comprendre les symptômes
- Consulter la documentation officielle si nécessaire

PHASE 2: INSPECTION SYSTÈME
- Vérifier configuration Claude Desktop
- Lire les fichiers sources du MCP
- Vérifier dépendances et environnement
- Tester les chemins et permissions

PHASE 3: ANALYSE & DIAGNOSTIC
- Effectuer tous les checks de la checklist
- Identifier tous les problèmes (critiques, warnings, info)
- Consulter la doc MCP pour solutions:
  * https://modelcontextprotocol.io/docs/tools/debugging
  * https://modelcontextprotocol.io/docs/tools/inspector
  * https://code.claude.com/docs/fr/mcp
- Rechercher problèmes connus sur GitHub issues

PHASE 4: SOLUTION & RÉPARATION
- Proposer solutions pour chaque problème
- Demander validation avant modifications
- Appliquer corrections si approuvé
- Tester après chaque correction

PHASE 5: VALIDATION & RAPPORT
- Vérifier `claude mcp list` (status Connected)
- Tester les handlers critiques
- Générer rapport complet avec:
  * Résumé exécutif
  * Checks système détaillés
  * Problèmes détectés
  * Solutions proposées/appliquées
  * Tests de validation
  * Recommandations

Utilise tous les outils disponibles:
- MCP Context7 pour chercher dans la documentation
- MCP Gemini pour rechercher des solutions web
- WebFetch pour consulter les docs officielles
- Bash pour tester les commandes
- Read/Write/Edit pour analyser/corriger les fichiers

IMPORTANT:
- Toujours commencer par `claude mcp list`
- Consulter la doc officielle en cas de doute
- Ne jamais modifier du code sans validation
- Fournir un rapport structuré et complet
```

Lance l'agent mcp-doctor maintenant avec ce prompt.
