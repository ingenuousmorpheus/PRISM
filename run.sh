#!/usr/bin/env bash
# ─── PRISM launcher (macOS / Linux) ──────────────────────────────
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "[PRISM] Creating virtual environment..."
  python3 -m venv .venv
fi
source .venv/bin/activate

echo "[PRISM] Installing dependencies..."
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
  echo "[PRISM] No .env found — copying .env.example. Edit it with your keys."
  cp .env.example .env
fi

echo
echo "────────────────────────────────────────────────────────────"
echo "  PRISM · opening http://127.0.0.1:7369"
echo "────────────────────────────────────────────────────────────"
(sleep 1 && (open http://127.0.0.1:7369 2>/dev/null || xdg-open http://127.0.0.1:7369 2>/dev/null)) &
python backend/server.py
