#!/usr/bin/env bash
# NPC Robot - Reverse Turing Test - Startup Script for macOS/Linux
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found! Creating one..."
    python3 -m venv .venv
    echo "Installing dependencies..."
    .venv/bin/pip install -r requirements.txt
fi
if [ ! -f ".env" ]; then
    echo ".env file not found! Copying .env.example..."
    cp .env.example .env
    echo "Please edit .env and add your OPENAI_API_KEY!"
    exit 1
fi
echo "Starting NPC Robot..."
.venv/bin/python cli/main.py
