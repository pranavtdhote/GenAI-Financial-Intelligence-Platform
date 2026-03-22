# EMERGENCY: Kill All Python/Uvicorn Processes
# Run this to stop ALL backend servers

Write-Host "Stopping ALL Python/Uvicorn processes..." -ForegroundColor Red
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "All processes stopped. Now run:" -ForegroundColor Green
Write-Host "  python -m uvicorn app.main:app --reload" -ForegroundColor Cyan
