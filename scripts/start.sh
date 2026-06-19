#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  echo "Virtual environment missing. Run: python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'"
  exit 1
fi

cd "$ROOT"
API_PID=""

cleanup() {
  if [[ -n "$API_PID" ]]; then
    kill "$API_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

if ! curl --silent --fail http://127.0.0.1:8000/health >/dev/null 2>&1; then
  "$PYTHON" -m uvicorn finagent.api.main:app --host 127.0.0.1 --port 8000 &
  API_PID=$!
  for _ in {1..30}; do
    curl --silent --fail http://127.0.0.1:8000/health >/dev/null 2>&1 && break
    sleep 0.25
  done
fi

echo "FinAgent AI is starting at http://localhost:8501"
"$PYTHON" -m streamlit run finagent/ui/app.py
