# Met a jour POSTGRES_PASSWORD dans le .env racine puis cree/reinitialise l'admin.
# Usage : .\scripts\set-db-password-and-admin.ps1
# Vous serez invite a saisir le mot de passe PostgreSQL.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path (Join-Path $root ".env"))) {
    Write-Host "[ERREUR] Fichier .env introuvable a la racine du projet."
    exit 1
}

$password = Read-Host "Mot de passe PostgreSQL (utilisateur postgres)" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
$plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)

if ([string]::IsNullOrWhiteSpace($plainPassword)) {
    Write-Host "[ERREUR] Mot de passe vide."
    exit 1
}

# Pour .env : entre guillemets, echapper \ et "
$escaped = $plainPassword.Replace('\', '\\').Replace('"', '\"')

$envPath = Join-Path $root ".env"
$content = Get-Content $envPath -Raw -Encoding UTF8
$content = $content -replace '(?m)^POSTGRES_PASSWORD=.*', "POSTGRES_PASSWORD=`"$escaped`""
[System.IO.File]::WriteAllText($envPath, $content, [System.Text.UTF8Encoding]::new($false))

Write-Host "POSTGRES_PASSWORD mis a jour dans .env"

Push-Location (Join-Path $root "services\api")
try {
    $out = python scripts/reset_admin_password.py 2>&1
    $out | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) {
        if ($out -match "Aucun utilisateur") {
            Write-Host "Creation de l'admin..."
            python scripts/create_admin.py
            if ($LASTEXITCODE -ne 0) { exit 1 }
        } else {
            exit 1
        }
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Connectez-vous sur http://localhost:3001/login avec :"
Write-Host "  Email/Telephone : admin@madavola.mg (ou 0340000000)"
Write-Host "  Mot de passe    : admin123"
