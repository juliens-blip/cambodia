# Configuration Git et Push vers GitHub

Write-Host "=== Configuration Git et Push ===" -ForegroundColor Cyan
Write-Host ""

# Configurer l'identité Git
Write-Host "Configuration de l'identité Git..." -ForegroundColor Yellow
git config --global user.name "juliens-blip"
git config --global user.email "juliens.blip@gmail.com"

# Vérifier la configuration
Write-Host "Identité configurée:" -ForegroundColor Green
git config user.name
git config user.email
Write-Host ""

# Stager tous les fichiers
Write-Host "Staging des fichiers..." -ForegroundColor Yellow
git add .

# Créer le commit
Write-Host "Création du commit..." -ForegroundColor Yellow
git commit -m "first commit" -m "" -m "🤖 Generated with [Claude Code](https://claude.com/claude-code)" -m "" -m "Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# S'assurer qu'on est sur main
Write-Host "Configuration de la branche main..." -ForegroundColor Yellow
git branch -M main

# Pousser vers GitHub
Write-Host "Push vers GitHub..." -ForegroundColor Yellow
git push -u origin main

Write-Host ""
Write-Host "=== SUCCÈS ===" -ForegroundColor Green
Write-Host "Votre projet est maintenant sur GitHub:" -ForegroundColor Cyan
Write-Host "https://github.com/juliens-blip/cambodia.git" -ForegroundColor Blue
Write-Host ""
