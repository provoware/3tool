#!/usr/bin/env bash
set -euo pipefail

python -m compileall -q .
python -m core.file_manifest --verify
python -m ruff check .
python -m black --check .
python -m mypy .
python -m pytest -q
