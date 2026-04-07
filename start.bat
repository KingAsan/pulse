@echo off
chcp 65001 >nul
title Pulse — Пульс развлечений

echo ==========================================
echo    Pulse — Пульс развлечений
echo ==========================================
echo.

cd /d "%~dp0backend"

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install Python 3.10+ from python.org
    pause
    exit /b 1
)

:: Check .env
if not exist ".env" (
    echo [!] File .env not found. Creating from .env.example...
    copy .env.example .env >nul
    echo [!] Fill in API keys in backend\.env and restart.
    notepad .env
    pause
    exit /b 1
)

:: Install dependencies
echo [1/3] Installing dependencies...
pip install -r requirements.txt -q

:: Run tests
echo [2/3] Running tests...
python -m pytest tests/ -q --tb=short
echo.

:: Start server
echo [3/3] Starting server...
echo.
echo    http://localhost:5000
echo.
echo    Press Ctrl+C to stop
echo ==========================================
python app.py
pause
