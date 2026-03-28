# Muni-Pal Startup Script
# Starts backend, Celery worker, and frontend for local development

$projectRoot = $PSScriptRoot

Write-Host "Starting Muni-Pal..." -ForegroundColor Cyan

# Start backend in a new PowerShell window
Write-Host "Starting backend on http://localhost:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "$projectRoot\scripts\start_backend.ps1", "-ListenHost", "127.0.0.1", "-ListenPort", "8000", "-Reload"

# Start Celery worker in a new PowerShell window
Write-Host "Starting Celery worker..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "$projectRoot\scripts\start_worker.ps1"

# Wait a moment for backend to initialize
Start-Sleep -Seconds 3

# Start frontend in a new PowerShell window
Write-Host "Starting frontend on http://localhost:3001..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$env:VITE_API_PROXY_TARGET='http://127.0.0.1:8000'; cd '$projectRoot\frontend'; npm run dev -- --host 127.0.0.1 --port 3001"

Write-Host ""
Write-Host "Muni-Pal is starting up!" -ForegroundColor Cyan
Write-Host "  Backend API:  http://localhost:8000/health" -ForegroundColor Yellow
Write-Host "  Celery:       scripts/start_worker.ps1" -ForegroundColor Yellow
Write-Host "  Frontend:     http://localhost:3001" -ForegroundColor Yellow
Write-Host ""
Write-Host "Three new PowerShell windows have opened for the servers."
Write-Host "Close those windows to stop the servers."
