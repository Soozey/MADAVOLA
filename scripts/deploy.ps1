# Script de déploiement PowerShell pour MADAVOLA
# Usage: .\scripts\deploy.ps1 [dev|prod]

param(
    [string]$Env = "prod"
)

$ErrorActionPreference = "Stop"

$ComposeFile = if ($Env -eq "dev") {
    "infra/docker/compose.yml"
} else {
    "infra/docker/compose.prod.yml"
}

Write-Host "🚀 Déploiement en mode: $Env" -ForegroundColor Cyan
Write-Host "📁 Fichier compose: $ComposeFile" -ForegroundColor Cyan

# Vérifier que le fichier .env existe
if (-not (Test-Path ".env")) {
    Write-Host "❌ Fichier .env non trouvé. Copiez env.example vers .env et configurez-le." -ForegroundColor Red
    exit 1
}

# Construire et démarrer les services
Write-Host "🔨 Construction des images..." -ForegroundColor Yellow
docker compose -f $ComposeFile build

Write-Host "🚀 Démarrage des services..." -ForegroundColor Yellow
docker compose -f $ComposeFile up -d

Write-Host "⏳ Attente du démarrage des services..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Vérifier la santé des services
Write-Host "🏥 Vérification de la santé des services..." -ForegroundColor Yellow
docker compose -f $ComposeFile ps

Write-Host "✅ Déploiement terminé!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Services disponibles:" -ForegroundColor Cyan
Write-Host "  - API: http://localhost:8000"
Write-Host "  - Web: http://localhost:80"
Write-Host "  - Nginx: http://localhost:8080"
