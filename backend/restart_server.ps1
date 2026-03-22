# Restart Backend Server Script
# This stops any running uvicorn processes and starts a fresh one

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Backend Server Restart - Groq Migration" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Stop all running uvicorn processes on port 8000
Write-Host "Step 1: Stopping old uvicorn processes..." -ForegroundColor Yellow
$processes = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*"
}

if ($processes) {
    $processes | ForEach-Object {
        Write-Host "  → Stopping process $($_.Id)..." -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
    Write-Host "  ✓ Old processes stopped" -ForegroundColor Green
} else {
    Write-Host "  → No running uvicorn processes found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Step 2: Clearing Python cache..." -ForegroundColor Yellow
Get-ChildItem -Path "app" -Filter "*.pyc" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force
Write-Host "  ✓ Cache cleared" -ForegroundColor Green

Write-Host ""
Write-Host "Step 3: Verifying Groq configuration..." -ForegroundColor Yellow
python check_provider.py
Write-Host ""

Write-Host "Step 4: Starting fresh uvicorn server with Groq..." -ForegroundColor Yellow
Write-Host "  → Server will start at http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "  → Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Start the server
python -m uvicorn app.main:app --reload
