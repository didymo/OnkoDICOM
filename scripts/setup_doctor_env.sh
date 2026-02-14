#!/usr/bin/env bash
set -euo pipefail

# One-command environment bootstrap for clinicians/testers.
# Uses Python 3.11 and an isolated Poetry runtime inside .venv to avoid
# host-level Poetry/Python mismatches.

if ! command -v python3.11 >/dev/null 2>&1; then
  echo "ERROR: python3.11 is required but not found in PATH."
  echo "Install it, then rerun this script."
  exit 1
fi

echo "[1/5] Recreating .venv with Python 3.11..."
rm -rf .venv
python3.11 -m venv .venv

echo "[2/5] Activating .venv..."
# shellcheck disable=SC1091
source .venv/bin/activate

echo "[3/5] Installing build tooling + Poetry in .venv..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install "poetry==1.8.5"

echo "[4/5] Installing project dependencies with Poetry..."
POETRY_VIRTUALENVS_CREATE=false poetry install --no-root

echo "[5/5] Verifying runtime dependencies..."
python -c "import batchgenerators; print('batchgenerators ok')"
if ! python -c "import radiomics; print('pyradiomics ok')" >/dev/null 2>&1; then
  python -m pip install --no-build-isolation "pyradiomics==3.0.1" || \
  python -m pip install "git+https://github.com/AIM-Harvard/pyradiomics.git"
fi
python -c "import radiomics; print('pyradiomics ok')"

echo
echo "Environment ready."
echo "Activate with: source .venv/bin/activate"
echo "Run app:      python main.py"
echo "Run tests:    pytest -q"
