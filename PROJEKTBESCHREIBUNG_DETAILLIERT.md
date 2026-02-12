# Projektbeschreibung (detailliert)

## Ziel
VideoBatchTool erzeugt aus Bild- und Audio-Dateien stapelweise Videos. Fokus ist **einfache Bedienung**, **Barrierefreiheit** und **sichere, nachvollziehbare Abläufe**.

## Kernfunktionen
- GUI für Bild-/Audio-Auswahl, Vorschau, Sortierung und Auto-Pairing.
- Mehrere Modi: Standard, Slideshow, Video+Audio, Mehrere Audios mit einem Bild.
- Persistente Logs mit verständlichen Meldungen und Fehlerhinweisen.
- Linux-konforme Dateinamens-Templates mit Metadaten (z. B. Länge, Qualität, Abmaße, Form).
- Verschieben/Kopieren verarbeiteter Dateien in `~/benutzte_dateien` mit `_benutzt`-Suffix.

## Barrierefreiheit (Accessibility)
- Hohe Kontraste, Fokus-Hervorhebung, klare Labels, Tastaturfreundlichkeit.
- Große Bedienelemente und einstellbare Schriftgröße.
- Laienfreundliche Sprache mit Hilfetexten.

## Erweiterbarkeit (Plugin-System)
- Plugins liegen zur Laufzeit in `~/.videobatchtool/plugins`.
- Jeder Plugin-Hook ist optional.
- Unterstützte Hooks:
  - `before_encode(payload)` kann den ffmpeg-Befehl anpassen.
  - `after_encode(payload)` wird nach erfolgreicher Ausgabe aufgerufen.

### Beispiel-Plugin
```python
# ~/.videobatchtool/plugins/mein_plugin.py

def before_encode(payload):
    cmd = payload.get("command", [])
    cmd += ["-metadata", "comment=plugin_aktiv"]
    payload["command"] = cmd
    return payload
```

## Vollautomatische Qualitätsprüfung
Empfohlene Projektprüfung:
```bash
scripts/quality_check.sh
pytest
```
Diese Kombination prüft Stil, statische Qualität und Funktionstests.

## Mega-Verbesserungsvorschlag
Ein **Assistenzmodus mit Live-Qualitätsampel**:
- Vor dem Start sieht man sofort eine Ampel pro Paar (grün/gelb/rot) für Lesbarkeit, Dateinamen-Qualität und Risiko auf Fehler.
- Mit einem Klick werden empfohlene Korrekturen automatisch angewendet (z. B. Kontrast-Theme aktivieren, Dateinamen normalisieren, fehlende Metadaten ergänzen).
- Für Laien erklärt ein Hilfefenster jede Ampel in einfacher Sprache.
