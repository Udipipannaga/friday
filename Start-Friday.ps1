param([switch]$Install)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$fridayPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if ($Install) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.14 is required.' }
    & $fridayPython -m pip install -r backend\requirements.lock.txt --cache-dir .cache\pip
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
    Push-Location frontend
    npm ci --cache ../.cache/npm
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    Pop-Location
}
if (-not (Test-Path $fridayPython)) { throw 'First run .\Start-Friday.ps1 -Install' }
if (-not (Test-Path frontend\dist\index.html)) { throw 'Build the UI first with .\Start-Friday.ps1 -Install' }
if (-not (Test-Path backend\.env)) { Copy-Item .env.example backend\.env }
Push-Location backend
& $fridayPython -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
$fridayWorker = Start-Process -FilePath $fridayPython -ArgumentList '-m','friday.execution' -WorkingDirectory (Get-Location).Path -WindowStyle Hidden -PassThru
Write-Host 'FRIDAY: http://localhost:8000 — press Ctrl+C to stop the API and local worker.'
try {
    & $fridayPython -m uvicorn friday.api:app --host 127.0.0.1 --port 8000 --no-access-log
} finally {
    if (-not $fridayWorker.HasExited) { Stop-Process -Id $fridayWorker.Id }
    Pop-Location
}
