#!/usr/bin/env bash
set -euo pipefail

echo "=== Telekom RAG Chatbot ==="

if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Copy .env.example and fill in your keys."
    exit 1
fi

echo "[1/4] Installing Python dependencies..."
uv sync --all-extras

echo "[2/4] Running data pipeline..."
PYTHONPATH=src uv run python -m data_pipeline.main

echo "[3/4] Starting backend..."
PYTHONPATH=src uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
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
