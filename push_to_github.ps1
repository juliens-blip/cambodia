# Script PowerShell pour pousser le projet vers GitHub
# Exécutez ce script APRÈS avoir fermé Claude Code

Write-Host "=== Push du projet Cambodia vers GitHub ===" -ForegroundColor Cyan
Write-Host ""

# Attendre 2 secondes pour s'assurer que les verrous sont libérés
Write-Host "Attente de la libération des verrous git..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

# Supprimer le fichier lock s'il existe encore
if (Test-Path ".git\index.lock") {
    Write-Host "Suppression du fichier lock..." -ForegroundColor Yellow
    Remove-Item -Force ".git\index.lock" -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# Stager tous les fichiers
Write-Host "Staging des fichiers..." -ForegroundColor Green
git add .

# Créer le commit initial
Write-Host "Création du commit initial..." -ForegroundColor Green
git commit -m "first commit" -m "" -m "🤖 Generated with [Claude Code](https://claude.com/claude-code)" -m "" -m "Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# S'assurer qu'on est sur la branche main
Write-Host "Configuration de la branche main..." -ForegroundColor Green
git branch -M main

# Pousser vers GitHub
Write-Host "Push vers GitHub..." -ForegroundColor Green
git push -u origin main

Write-Host ""
Write-Host "=== TERMINÉ ===" -ForegroundColor Cyan
Write-Host "Votre projet est maintenant disponible sur:" -ForegroundColor Green
Write-Host "https://github.com/juliens-blip/cambodia.git" -ForegroundColor Blue
Write-Host ""
Write-Host "Appuyez sur une touche pour continuer..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
