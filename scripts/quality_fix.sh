#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/_quality_common.sh"

qb_run_python_check "QA-Preflight (Abhaengigkeiten + Tool-Importe)" core.qa_preflight --requirements requirements-dev.txt --tools ruff black mypy pytest flake8 isort autoflake --report-json data/runtime/qa_preflight_report.json

qb_print_step "✨" "Wende Auto-Fixes nur auf getrackte Projektdateien an..."
qb_tracked_python_files
qb_run_python_check "Auto-Fix Linting (ruff --fix)" ruff check --fix "${QB_TRACKED_PYTHON_FILES[@]}"
qb_run_python_check "Auto-Fix ungenutzte Importe (autoflake)" autoflake --remove-all-unused-imports --in-place "${QB_TRACKED_PYTHON_FILES[@]}"
qb_run_python_check "Imports sortieren (isort)" isort "${QB_TRACKED_PYTHON_FILES[@]}"
qb_run_python_check "Code formatieren (black)" black "${QB_TRACKED_PYTHON_FILES[@]}"
qb_run_python_check "Linting nach Auto-Fix (flake8)" flake8 --extend-ignore E501 .
qb_run_python_check "Typprüfung nach Auto-Fix (mypy)" mypy .
qb_run_python_check "Tests nach Auto-Fix (pytest)" pytest -q

qb_print_step "✅" "Auto-Fixes und Tests erfolgreich abgeschlossen."
