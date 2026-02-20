# Muni-Pal Startup Script
# Starts both backend (port 8080) and frontend (port 3000)

$projectRoot = $PSScriptRoot

Write-Host "Starting Muni-Pal..." -ForegroundColor Cyan

# Start backend in a new PowerShell window
Write-Host "Starting backend on http://localhost:8080..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; python -m uvicorn munipal.main:app --reload --host 127.0.0.1 --port 8080"

# Wait a moment for backend to initialize
Start-Sleep -Seconds 3

# Start frontend in a new PowerShell window
Write-Host "Starting frontend on http://localhost:3000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\frontend'; npm run dev"

Write-Host ""
Write-Host "Muni-Pal is starting up!" -ForegroundColor Cyan
Write-Host "  Backend API:  http://localhost:8080/docs" -ForegroundColor Yellow
Write-Host "  Frontend:     http://localhost:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Two new PowerShell windows have opened for the servers."
Write-Host "Close those windows to stop the servers."
