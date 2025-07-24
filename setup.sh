# Muster für setup.sh
# Dieses Skript richtet die Umgebung ein und testet das Tool.
# 1. Virtuelle Umgebung (getrennter Python-Arbeitsbereich) erstellen
python3 -m venv .venv
# 2. Aktivieren (Linux/macOS)
source .venv/bin/activate
# 3. Benötigte Pakete installieren
pip install -r requirements.txt
# 4. Optionale Selbsttests starten
python3 videobatch_extra.py --selftest
# 5. GUI über den Launcher starten
python3 videobatch_launcher.py
