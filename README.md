# VideoBatchTool

Dieses Projekt erstellt aus Bildern und Audiodateien einfache Videos im MP4-Format. Die grafische Oberflaeche (GUI) hilft beim Paaren der Dateien und beim Starten der Verarbeitung.

## Voraussetzungen

* Python 3.10 oder neuer
* `ffmpeg` und `ffprobe` muessen im Systempfad vorhanden sein

Die benoetigten Python-Pakete stehen in `requirements.txt`.

## Schnellstart

1. Python-Abhaengigkeiten installieren:
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

Weitere Erklaerungen fuer Einsteiger finden sich in `ANLEITUNG_EINSTEIGER.md`.
Zusätzliche Tipps stehen in `ANLEITUNG_TIPPS.md`.
Noch mehr Hinweise bietet `ANLEITUNG_WEITER.md`.
Weitere Beispiele gibt es in `ANLEITUNG_MEHR.md`.
Ergänzende Vorschläge enthält `ANLEITUNG_ZUSATZ.md`.
Weitere Befehle zeigt `ANLEITUNG_EXTRA_BEFEHLE.md`.
Hinweise zu den neuen Modi finden sich in `ANLEITUNG_MODI.md`.
Praktische Beispiele liefert `ANLEITUNG_PRAKTISCH.md`.

## Zusaetzlich

* Die Datei `videobatch_extra.py` enthaelt eine Kommandozeilenversion. Mit `--selftest` lassen sich einfache Tests ausfuehren.
* In `0000-testall` liegt ein Beispielskript, um Prueftools wie `flake8` oder `black` einzurichten.
* Ereignisse und Aenderungen werden in `ereignislog.txt` festgehalten.

Weitere Hinweise finden sich in den Kommentaren der Python-Dateien.
