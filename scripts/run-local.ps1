# Lancer l'API en local (sans Docker pour l'API).
# Prérequis : base PostgreSQL (Docker : docker compose -f infra/docker/compose.dev-db-only.yml up -d)
# Puis : cd apps/web && npm run dev (autre terminal)

$ErrorActionPreference = "Stop"
$ApiDir = Join-Path $PSScriptRoot ".." "services" "api"

if (-not (Test-Path (Join-Path $ApiDir ".env"))) {
    $Example = Join-Path $ApiDir "env.example.local"
    if (Test-Path $Example) {
        Copy-Item $Example (Join-Path $ApiDir ".env")
        Write-Host "Fichier .env créé depuis env.example.local." -ForegroundColor Yellow
    } else {
        Write-Host "Creez services/api/.env avec DATABASE_URL et JWT_SECRET (voir README)." -ForegroundColor Red
        exit 1
    }
}

Set-Location $ApiDir
Write-Host "Demarrage API sur http://localhost:8000" -ForegroundColor Cyan
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
