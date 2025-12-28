# Script pour réinitialiser git et pousser sans les secrets

Write-Host "=== Nettoyage de l'historique Git ===" -ForegroundColor Cyan
Write-Host ""

# 1. Sauvegarder la configuration du remote
$remoteUrl = git remote get-url origin
Write-Host "Remote URL sauvegardé: $remoteUrl" -ForegroundColor Green

# 2. Supprimer complètement le dossier .git
Write-Host "Suppression de l'historique git..." -ForegroundColor Yellow
Remove-Item -Recurse -Force .git

# 3. Réinitialiser git
Write-Host "Réinitialisation de git..." -ForegroundColor Yellow
git init

# 4. Configurer l'identité
Write-Host "Configuration de l'identité..." -ForegroundColor Yellow
git config user.name "juliens-blip"
git config user.email "julien.simard31@gmail.com"

# 5. Ajouter le remote
Write-Host "Ajout du remote..." -ForegroundColor Yellow
git remote add origin $remoteUrl

# 6. Créer la branche main
Write-Host "Configuration de la branche main..." -ForegroundColor Yellow
git branch -M main

# 7. Stager tous les fichiers (sans les secrets)
Write-Host "Staging des fichiers nettoyés..." -ForegroundColor Yellow
git add .

# 8. Créer le commit initial propre
Write-Host "Création du commit initial..." -ForegroundColor Yellow
git commit -m "first commit - Cambodia Agri Analytics Platform

Multi-commodity analytics platform for Cashew and Rubber markets in Cambodia.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 9. Force push vers GitHub
Write-Host "Force push vers GitHub..." -ForegroundColor Yellow
git push -u origin main --force

Write-Host ""
Write-Host "=== SUCCÈS ===" -ForegroundColor Green
Write-Host "Projet poussé sur GitHub sans secrets!" -ForegroundColor Cyan
Write-Host "https://github.com/juliens-blip/cambodia.git" -ForegroundColor Blue
Write-Host ""
