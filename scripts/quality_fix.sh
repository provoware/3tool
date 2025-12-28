#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Installiere Prüftools..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-dev.txt

echo "✨ Wende Auto-Fixes an..."
python3 -m ruff check --fix .
python3 -m black .
python3 -m unittest discover -s tests -p "test_*.py"
