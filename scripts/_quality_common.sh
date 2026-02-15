#!/usr/bin/env bash
set -euo pipefail

qb_print_step() {
  local icon="$1"
  local text="$2"
  if [[ -z "${icon}" || -z "${text}" ]]; then
    echo "❌ Interner Fehler: qb_print_step braucht Icon und Text." >&2
    return 1
  fi
  echo "${icon} ${text}"
}

qb_require_file() {
  local path="$1"
  if [[ -z "${path}" ]]; then
    echo "❌ Interner Fehler: Dateipfad fehlt." >&2
    return 1
  fi
  if [[ ! -f "${path}" ]]; then
    echo "❌ Benötigte Datei fehlt: ${path}" >&2
    echo "💡 Bitte Projekt vollständig klonen oder Datei wiederherstellen." >&2
    return 1
  fi
}

qb_require_command() {
  local cmd="$1"
  if [[ -z "${cmd}" ]]; then
    echo "❌ Interner Fehler: Kommando-Name fehlt." >&2
    return 1
  fi
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "❌ Benötigtes Kommando nicht gefunden: ${cmd}" >&2
    echo "💡 Bitte ${cmd} installieren und den Check erneut ausführen." >&2
    return 1
  fi
}

qb_install_dev_deps() {
  local requirements_file="$1"
  qb_require_file "${requirements_file}"
  qb_require_command python3

  qb_print_step "🔎" "Installiere/aktualisiere Prüftools..."
  python3 -m pip install --upgrade pip
  python3 -m pip install -r "${requirements_file}"
  qb_print_step "✅" "Prüftools sind bereit."
}

qb_run_python_check() {
  local label="$1"
  shift
  if [[ -z "${label}" ]]; then
    echo "❌ Interner Fehler: Label fehlt für qb_run_python_check." >&2
    return 1
  fi
  qb_print_step "🧪" "${label}"
  python3 -m "$@"
}
