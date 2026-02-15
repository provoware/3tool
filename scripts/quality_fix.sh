#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/_quality_common.sh"

qb_run_python_check "QA-Preflight (Abhaengigkeiten + Tool-Importe)" core.qa_preflight --requirements requirements-dev.txt --tools ruff black mypy pytest

qb_print_step "✨" "Wende Auto-Fixes an..."
qb_run_python_check "Auto-Fix Linting (ruff --fix)" ruff check --fix .
qb_run_python_check "Code formatieren (black)" black .
qb_run_python_check "Typprüfung nach Auto-Fix (mypy)" mypy .
qb_run_python_check "Tests nach Auto-Fix (pytest)" pytest -q

qb_print_step "✅" "Auto-Fixes und Tests erfolgreich abgeschlossen."
