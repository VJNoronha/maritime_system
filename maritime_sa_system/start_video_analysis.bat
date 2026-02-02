@echo off
REM Maritime Video Analysis System - Quick Start (Windows)

echo ==================================================
echo Maritime Video Analysis System - Quick Start
echo ==================================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo X Python is not installed
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Install dependencies
echo [*] Installing dependencies (including OpenCV)...
pip install -q -r requirements.txt

if %errorlevel% neq 0 (
    echo X Failed to install dependencies
    pause
    exit /b 1
)

echo [OK] Dependencies installed
echo.

echo ==================================================
echo [*] Starting Video Analysis Server...
echo ==================================================
echo.
echo The dashboard will be available at:
echo    http://localhost:5000
echo.
echo Features:
echo   * Upload maritime video files (MP4, AVI, MOV, etc.)
echo   * Real-time SA layer analysis
echo   * Anomaly detection from video
echo   * Spoofing detection
echo   * Live alerts and statistics
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start server
cd backend
python video_server.py

pause
