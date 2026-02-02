@echo off
REM Maritime Situation Awareness Layer - Quick Start Script (Windows)

echo ==================================================
echo Maritime Situation Awareness Layer - Quick Start
echo ==================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo X Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Install dependencies
echo [*] Installing dependencies...
pip install -q -r requirements.txt

if %errorlevel% neq 0 (
    echo X Failed to install dependencies
    pause
    exit /b 1
)

echo [OK] Dependencies installed successfully
echo.

REM Run tests
echo [*] Running system tests...
cd backend
python test_system.py

if %errorlevel% neq 0 (
    echo.
    echo X System tests failed. Please check the output above.
    pause
    exit /b 1
)

echo.
echo [OK] All tests passed!
echo.
echo ==================================================
echo [*] Starting Demo Server...
echo ==================================================
echo.
echo The dashboard will be available at:
echo    http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
python demo_server.py

pause
