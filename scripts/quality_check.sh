#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/_quality_common.sh"

qb_run_python_check "QA-Preflight (Abhaengigkeiten + Tool-Importe)" core.qa_preflight --requirements requirements-dev.txt --tools ruff black mypy pytest flake8 isort autoflake

qb_print_step "✅" "Starte Code-Checks..."
qb_run_python_check "Syntax-Check (compileall)" compileall -q .
qb_run_python_check "Manifest-Integrität prüfen" core.file_manifest --verify
qb_run_python_check "Linting (ruff)" ruff check .
qb_run_python_check "Linting (flake8)" flake8 --extend-ignore E501 .
qb_run_python_check "Import-Tool verfuegbar (isort --version-number)" isort --version-number
qb_run_python_check "Formatprüfung (black --check)" black --check .
qb_run_python_check "Typprüfung (mypy)" mypy .
qb_run_python_check "Tests (pytest)" pytest -q

qb_print_step "✅" "Alle Quality-Checks erfolgreich abgeschlossen."
