@echo off
REM AI Employee Dashboard - Quick Start Script

echo =========================================
echo   AI Employee Dashboard - Starting...
echo =========================================
echo.

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.8+ and add to PATH
    pause
    exit /b 1
)

REM Install dependencies if needed
if not exist "__pycache__" (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    echo.
)

REM Get VM IP address
echo Getting network information...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set "IP=%%a"
    goto :found
)
:found

echo.
echo =========================================
echo   Dashboard is starting...
echo =========================================
echo.
echo   Local Access:  http://localhost:5000
echo   Network Access: http:%IP%:5000
echo.
echo   Press Ctrl+C to stop
echo.
echo =========================================
echo.

REM Start the dashboard
python app.py
