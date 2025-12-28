param(
    [switch]$Seed,
    [switch]$StartChroma
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $ProjectRoot ".venv311\\Scripts\\python.exe"

if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

$env:API_URL = "http://127.0.0.1:8000"

if ($StartChroma) {
    $ComposeFile = Join-Path $ProjectRoot "docker-compose.yml"
    if (Test-Path $ComposeFile) {
        docker-compose -f $ComposeFile up -d
    }
}

if ($Seed) {
    & $PythonExe (Join-Path $ProjectRoot "scripts\\seed_collectors.py")
}

Start-Process -FilePath $PythonExe -WorkingDirectory $ProjectRoot -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"
Start-Process -FilePath $PythonExe -WorkingDirectory $ProjectRoot -ArgumentList "-m", "streamlit", "run", "dashboard/app.py", "--server.port", "8501"

Write-Host "API: http://127.0.0.1:8000"
Write-Host "Dashboard: http://127.0.0.1:8501"
