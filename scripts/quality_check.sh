#!/usr/bin/env bash
set -euo pipefail

echo "🔎 Installiere Prüftools..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-dev.txt

echo "✅ Starte Code-Checks..."
python3 -m compileall -q .
python3 -m ruff check .
python3 -m black --check .
python3 -m unittest discover -s tests -p "test_*.py"
