#!/usr/bin/env bash
# Vorlage (Template): lokale Einrichtung für Entwickler
set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_ROOT"

python3 -m venv .videotool_env
# shellcheck disable=SC1091
source .videotool_env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python3 videobatch_extra.py --selftest
python3 start_gui.py
