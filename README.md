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
   Der Launcher legt bei Bedarf automatisch ein virtuelles Umfeld ("virtual environment") an,
   installiert die Pakete und führt einen kurzen Selbsttest aus. Danach startet die grafische Oberfläche.

Eine ausfuehrliche Anleitung mit allen Tipps steht in `ANLEITUNG_GESAMT.md`.
Weitere einfache Beispiele bietet `ANLEITUNG_LAIENPLUS.md`.
Im Abschnitt "Weiterführende Befehle" von `ANLEITUNG_GESAMT.md` finden sich
zusätzliche Kommandos für neugierige Einsteiger.
Weitere Beispiele stehen in `ANLEITUNG_EXTRA.md`.
Noch mehr Befehle zeigt `ANLEITUNG_WEITERE_TIPPS.md`.
Profis finden zusätzliche Hinweise in `ANLEITUNG_PROFI.md`.

Unterstuetzte Modi:
* **Standard** – ein Bild pro Audio
* **Slideshow** – ganzer Bilder-Ordner fuer jedes Audio
* **Video + Audio** – vorhandenes Video mit neuer Tonspur
* **Mehrere Audios, ein Bild** – gleiches Bild fuer viele Audiodateien
Weitere Erklaerungen fuer Einsteiger finden sich in `ANLEITUNG_EINSTEIGER.md`.
Zusätzliche Tipps stehen in `ANLEITUNG_TIPPS.md`.

## Zusaetzlich

* Die Datei `videobatch_extra.py` enthaelt eine Kommandozeilenversion. Mit `--selftest` lassen sich einfache Tests ausfuehren.
* In `0000-testall` liegt ein Beispielskript, um Prueftools wie `flake8` oder `black` einzurichten.
* Ereignisse und Aenderungen werden in `ereignislog.txt` festgehalten.

Weitere Hinweise finden sich in den Kommentaren der Python-Dateien.
