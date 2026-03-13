param(
    [switch]$Fix
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root

if ($Fix) { $mode = 'CHECK+FIX' } else { $mode = 'CHECK' }
Write-Host '== MADAVOLA Encoding Check ==' -ForegroundColor Cyan
Write-Host "Root: $root"
Write-Host "Mode: $mode"

$excludeRegex = '\\node_modules\\|\\.git\\|\\dist\\|\\build\\|\\coverage\\|\\test-results\\|\\.venv\\|\\__pycache__\\'
$textExt = @(
    '.ts','.tsx','.js','.jsx','.mjs','.cjs','.json','.md','.yml','.yaml','.toml','.ini','.cfg','.txt',
    '.py','.sql','.sh','.ps1','.css','.scss','.sass','.less','.html','.htm','.xml','.env','.example',
    '.php','.vue','.blade','.blade.php'
)
$viewExt = @('.html','.htm','.php','.vue','.blade','.blade.php')

$allFiles = Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notmatch $excludeRegex }
$textFiles = $allFiles | Where-Object {
    $ext = $_.Extension.ToLowerInvariant()
    ($textExt -contains $ext) -or ($_.Name -match '^\.(env|gitignore|editorconfig)$')
}
$viewFiles = $allFiles | Where-Object {
    $ext = $_.Extension.ToLowerInvariant()
    $viewExt -contains $ext
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$mojiFiles = New-Object System.Collections.Generic.List[string]
$bomFiles = New-Object System.Collections.Generic.List[string]
$missingMeta = New-Object System.Collections.Generic.List[string]
$changed = 0

$chC3 = [char]0x00C3
$chC2 = [char]0x00C2
$replacementChar = [char]0xFFFD

foreach ($f in $textFiles) {
    $path = $f.FullName
    $raw = [System.IO.File]::ReadAllText($path)

    if ($raw.Contains([string]$chC3) -or $raw.Contains([string]$chC2) -or $raw.Contains([string]$replacementChar)) {
        $mojiFiles.Add($path)
    }

    $fs = [System.IO.File]::OpenRead($path)
    try {
        $b = New-Object byte[] 3
        $n = $fs.Read($b, 0, 3)
        if ($n -eq 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF) {
            $bomFiles.Add($path)
            if ($Fix) {
                [System.IO.File]::WriteAllText($path, $raw, $utf8NoBom)
                $changed++
            }
        }
    } finally {
        $fs.Dispose()
    }
}

if ($Fix) {
    foreach ($f in $viewFiles) {
        $path = $f.FullName
        $raw = [System.IO.File]::ReadAllText($path)
        $updated = $raw

        if (($f.Extension -match '^\.(html|htm)$') -and ($updated -notmatch '(?i)<meta\s+charset\s*=')) {
            if ($updated -match '(?i)<head[^>]*>') {
                $updated = [System.Text.RegularExpressions.Regex]::Replace(
                    $updated,
                    '(?i)(<head[^>]*>)',
                    '$1' + [Environment]::NewLine + '    <meta charset="UTF-8" />',
                    1
                )
            }
        }

        if ($updated -ne $raw) {
            [System.IO.File]::WriteAllText($path, $updated, $utf8NoBom)
            $changed++
        }
    }
}

foreach ($vf in $viewFiles) {
    $content = [System.IO.File]::ReadAllText($vf.FullName)
    if (($vf.Extension -match '^\.(html|htm)$') -and ($content -notmatch '(?i)<meta\s+charset\s*=')) {
        $missingMeta.Add($vf.FullName)
    }
}

$dbCharsetOk = $false
$dbFile = Join-Path $root 'services/api/app/db.py'
if (Test-Path $dbFile) {
    $dbTxt = [System.IO.File]::ReadAllText($dbFile)
    if ($dbTxt -match 'client_encoding=UTF8') {
        $dbCharsetOk = $true
    }
}

Write-Host ''
Write-Host "Scanned text files : $($textFiles.Count)"
Write-Host "Scanned view files : $($viewFiles.Count)"
Write-Host "Mojibake files     : $($mojiFiles.Count)"
Write-Host "BOM files          : $($bomFiles.Count)"
Write-Host "Missing meta UTF-8 : $($missingMeta.Count)"
Write-Host "DB UTF-8 forced    : $dbCharsetOk"
if ($Fix) { Write-Host "Files changed      : $changed" }

if ($mojiFiles.Count -gt 0) {
    Write-Host ''
    Write-Host 'Mojibake detected:' -ForegroundColor Yellow
    $mojiFiles | Select-Object -First 50 | ForEach-Object { Write-Host " - $_" }
}

if ($bomFiles.Count -gt 0) {
    Write-Host ''
    Write-Host 'BOM detected:' -ForegroundColor Yellow
    $bomFiles | Select-Object -First 50 | ForEach-Object { Write-Host " - $_" }
}

if ($missingMeta.Count -gt 0) {
    Write-Host ''
    Write-Host 'Missing meta charset:' -ForegroundColor Yellow
    $missingMeta | ForEach-Object { Write-Host " - $_" }
}

$ok = ($mojiFiles.Count -eq 0 -and $bomFiles.Count -eq 0 -and $missingMeta.Count -eq 0 -and $dbCharsetOk)
if (-not $ok) {
    Write-Host ''
    Write-Host 'Encoding check FAILED.' -ForegroundColor Red
    exit 1
}

Write-Host ''
Write-Host 'Encoding check PASSED.' -ForegroundColor Green
exit 0
