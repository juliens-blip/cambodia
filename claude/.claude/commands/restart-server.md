# Restart Development Server

Relance automatiquement le serveur de développement Next.js après des modifications.

## Instructions

Tu dois exécuter les étapes suivantes pour relancer le serveur:

### 1. Arrêter le serveur actuel

- Sur Windows, identifier le processus Node.js écoutant sur le port 3000 (ou 3001, 3002)
- Utiliser `netstat -ano | findstr :3000` pour trouver le PID
- Tuer le processus avec `taskkill /F /PID <pid>`
- Attendre 2 secondes pour que le port se libère

### 2. Nettoyer les caches (si option --clean détectée)

Si l'utilisateur a fourni l'option `--clean`:
- Supprimer le dossier `.next`: `rmdir /s /q .next`
- Supprimer le cache de node_modules: `rmdir /s /q node_modules\.cache`

### 3. Démarrer le serveur

Selon l'option fournie:
- Par défaut ou sans option: `npm run dev`
- Avec option `--prod`: `npm run build` puis `npm start`

Lance le serveur en arrière-plan avec `run_in_background: true`

### 4. Valider le démarrage

- Attendre 5 secondes
- Vérifier les logs du processus en arrière-plan
- Identifier le port utilisé (généralement 3000, mais peut être 3001 ou 3002 si occupé)
- Si erreur dans les logs, l'afficher et proposer une solution
- Si OK, afficher un message de succès

### 5. Afficher le résultat

Format attendu:
```
🔄 Redémarrage du serveur...

✅ Serveur relancé avec succès!

📍 Port: 3000
🌐 URL: http://localhost:3000
📊 Statut: RUNNING ✅
```

En cas d'erreur:
```
❌ Erreur lors du démarrage du serveur

Erreur: [message d'erreur]

💡 Solution suggérée:
[suggestion basée sur l'erreur]
```

## Gestion des erreurs courantes

- **Port déjà utilisé**: Suggérer de tuer manuellement le processus ou d'utiliser un autre port
- **Erreur de compilation**: Afficher l'erreur TypeScript/ESLint et suggérer `npm run lint`
- **Module manquant**: Suggérer `npm install`
- **Cache corrompu**: Suggérer d'utiliser l'option `--clean`

## Notes importantes

- Sur Windows, utiliser les commandes Windows (taskkill, rmdir, findstr)
- Toujours vérifier que le processus est bien arrêté avant de relancer
- Ne pas utiliser CTRL+C ou des signaux UNIX sur Windows
- Gérer le cas où aucun serveur n'est en cours d'exécution (ne pas échouer)
