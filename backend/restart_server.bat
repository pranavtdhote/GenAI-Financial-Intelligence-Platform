@echo off
REM Restart Backend Server - Windows Batch Version
echo ==================================================
echo   Backend Server Restart - Groq Migration
echo ==================================================
echo.

echo Step 1: Stopping old uvicorn processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
timeout /t 2 /nobreak >nul
echo   Done
echo.

echo Step 2: Clearing Python cache...
del /s /q app\__pycache__\*.pyc 2>nul
echo   Done
echo.

echo Step 3: Verifying Groq configuration...
python check_provider.py
echo.

echo Step 4: Starting fresh uvicorn server with Groq...
echo   Server will start at http://127.0.0.1:8000
echo   Press Ctrl+C to stop the server
echo.
echo ==================================================
echo.

python -m uvicorn app.main:app --reload
