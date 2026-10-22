# Refresh from nflverse and compare challenger models on full historical seasons.
# Run from the repository root on a Python 3.13 installation.
$ErrorActionPreference = 'Stop'
$python = if (Test-Path '.venv\Scripts\python.exe') { '.\.venv\Scripts\python.exe' } else { 'py' }
if ($python -eq 'py') {
    & py -3.13 -m backend.modeling --refresh
    if ($LASTEXITCODE -ne 0) { throw 'Model refresh failed' }
    & py -3.13 -m backend.research
} else {
    & $python -m backend.modeling --refresh
    if ($LASTEXITCODE -ne 0) { throw 'Model refresh failed' }
    & $python -m backend.research
}
if ($LASTEXITCODE -ne 0) { throw 'Research evaluation failed' }
Write-Output 'Refresh finished. Inspect artifacts/evaluation.json and artifacts/research_report.json before publishing.'
