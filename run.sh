#!/usr/bin/env bash
set -euo pipefail

echo "=== Telekom RAG Chatbot ==="
echo ""

if [ ! -f .env ]; then
    echo "ERROR: .env file not found."
    echo "  cp .env.example .env"
    echo "  Then fill in your API keys."
    exit 1
fi

# Try Docker first, fall back to local
if command -v docker &>/dev/null && docker info &>/dev/null && docker compose version &>/dev/null; then
    echo "Starting with Docker Compose..."
    echo ""
    docker compose up --build
else
    echo "Docker not available — running locally."
    echo ""

    set -a && source .env && set +a
    export PYTHONPATH=src

    echo "[1/4] Installing Python dependencies..."
    uv sync --all-extras

    echo "[2/4] Running data pipeline..."
    uv run python -m data_pipeline.main

    echo "[3/4] Starting backend..."
    uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!

    echo "[4/4] Starting frontend..."
    cd src/frontend
    npm install --silent
    npm run dev &
    FRONTEND_PID=$!
    cd ../..

    echo ""
    echo "Backend:  http://localhost:8000"
    echo "Frontend: http://localhost:3000"
    echo "API docs: http://localhost:8000/docs"
    echo ""
    echo "Test account: username=test, password=test"
    echo "Press Ctrl+C to stop all services."

    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
    wait
fi
