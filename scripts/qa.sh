#!/usr/bin/env bash
set -euo pipefail

python -m core.qa_preflight --requirements requirements-dev.txt --tools ruff black mypy pytest flake8 isort autoflake --report-json data/runtime/qa_preflight_report.json
python -m compileall -q .
python -m core.file_manifest --verify
python -m ruff check .
python -m black --check .
python -m mypy .
python -m pytest -q
