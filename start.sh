#!/bin/bash
echo "=========================================="
echo "   Pulse — Пульс развлечений"
echo "=========================================="
echo

cd "$(dirname "$0")/backend"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found! Install Python 3.10+"
    exit 1
fi

# Check .env
if [ ! -f ".env" ]; then
    echo "[!] File .env not found. Creating from .env.example..."
    cp .env.example .env
    echo "[!] Fill in API keys in backend/.env and restart."
    exit 1
fi

# Install dependencies
echo "[1/3] Installing dependencies..."
pip3 install -r requirements.txt -q

# Run tests
echo "[2/3] Running tests..."
python3 -m pytest tests/ -q --tb=short
echo

# Start server
echo "[3/3] Starting server..."
echo
echo "   http://localhost:5000"
echo
echo "   Press Ctrl+C to stop"
echo "=========================================="
python3 app.py
