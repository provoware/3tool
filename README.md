# VideoBatchTool

Dieses Projekt erstellt aus Bildern und Audiodateien einfache Videos im MP4-Format. Die grafische Oberfläche (GUI) hilft beim Paaren der Dateien und beim Starten der Verarbeitung.

## Voraussetzungen

* Python 3.10 oder neuer
* `ffmpeg` und `ffprobe` müssen im Systempfad vorhanden sein

Die benötigten Python-Pakete stehen in `requirements.txt`.

## Schnellstart

1. Python-Abhängigkeiten installieren:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Das Tool starten:
   ```bash
   python3 videobatch_launcher.py
   ```
   Der Launcher legt bei Bedarf automatisch ein virtuelles Umfeld ("virtual environment") an und installiert die Pakete.

## Zusätzlich

* Die Datei `videobatch_extra.py` enthält eine Kommandozeilenversion. Mit `--selftest` können einfache Tests ausgeführt werden.
* In `0000-testall` befindet sich ein Beispielskript, um Prüfwerkzeuge wie `flake8` oder `black` einzurichten.

Weitere Hinweise finden sich in den Kommentaren der Python-Dateien.
