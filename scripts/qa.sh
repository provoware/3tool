#!/usr/bin/env bash
set -euo pipefail

python -m ruff check .
python -m black --check .
python -m mypy .
python -m pytest -q
