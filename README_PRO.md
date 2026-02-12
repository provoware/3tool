# VideoBatchTool Profi-Funktionen

## 1) Neuer Klick-Start

```bash
python3 start_gui.py --auto-repair --simple-mode
```

- prüft Python, venv/pip, Pakete, Schreibrechte und FFmpeg.
- kann automatisch reparieren (`--auto-repair`).
- startet danach die GUI robust mit klaren Fehlermeldungen.

## 2) Verbesserte CLI

```bash
python3 videobatch_extra_improved.py --mode slideshow --img ./bilder --aud ./ton.mp3 --out ./out --verbose
```

- klare Eingabeprüfung
- verständliche Konsolentexte
- `--verbose` für Diagnose

## 3) Professional CLI (Batch)

Manifest-Beispiel (`jobs.json`):

```json
[
  {"mode": "video", "source": "./input/video1.mp4", "audio": "./input/a1.mp3"},
  {"mode": "slideshow", "source": "./input/bilder", "audio": "./input/a2.mp3"}
]
```

Start:

```bash
python3 videobatch_professional.py --manifest jobs.json --out ./out --threads 4 --metadata-out metadata.json
```

- Batch-Workflows
- Parallelisierung über Threads
- JSON-Metadaten-Export
