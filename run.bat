@echo off
REM ─── PRISM launcher (Windows) ───────────────────────────────────
cd /d "%~dp0"

if not exist ".venv" (
  echo [PRISM] Creating virtual environment...
  python -m venv .venv
)
call .venv\Scripts\activate.bat

echo [PRISM] Installing dependencies...
pip install -q -r requirements.txt

if not exist ".env" (
  echo [PRISM] No .env found — copying .env.example. Edit it with your keys.
  copy .env.example .env >nul
)

echo.
echo ────────────────────────────────────────────────────────────
echo   PRISM · opening http://127.0.0.1:7369
echo ────────────────────────────────────────────────────────────
start "" "http://127.0.0.1:7369"
python backend\server.py
pause
