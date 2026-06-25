@echo off
REM NPC Robot - Reverse Turing Test - Startup Script for Windows
cd /d "%~dp0"
if not exist ".venv" (
    echo Virtual environment not found! Creating one...
    python -m venv .venv
    echo Installing dependencies...
    .venv\Scripts\pip install -r requirements.txt
)
if not exist ".env" (
    echo .env file not found! Copying .env.example...
    copy .env.example .env
    echo Please edit .env and add your OPENAI_API_KEY!
    pause
    exit /b 1
)
echo Starting NPC Robot...
.venv\Scripts\python cli/main.py
pause
