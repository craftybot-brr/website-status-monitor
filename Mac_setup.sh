#!/usr/bin/env bash
# Setup script for Website Status Monitor on macOS
set -euo pipefail

# ---------- Helpers ----------
has() { command -v "$1" >/dev/null 2>&1; }

# ---------- Homebrew ----------
if ! has brew; then
  echo "⏳  Homebrew not found; installing…"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Add brew to this shell’s PATH (Apple Silicon default path; Intel fallback below)
  eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || true)"
  eval "$(/usr/local/bin/brew shellenv 2>/dev/null || true)"
fi

echo "🔄  Updating Homebrew & formulas…"
brew update --quiet

# ---------- Python ----------
if ! has python3; then
  echo "⬇️  Installing Python 3 via Homebrew…"
  brew install python  # installs current python@3.x and pip3
fi

# Ensure venv module is present (part of stdlib since 3.3)
python3 - <<'PY'
import sys, ensurepip, venv, subprocess, pathlib, os
root = pathlib.Path(__file__).resolve().parent
venv_dir = root / "venv"
if not venv_dir.exists():
    print("🐍  Creating virtual environment…")
    venv.create(venv_dir, with_pip=True, clear=False)
print("✅  venv ready at", venv_dir)
PY

# ---------- Activate & install deps ----------
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo
echo "🎉  Setup complete."
echo "   Activate with:  source venv/bin/activate"
echo "   Run server:     python app.py"