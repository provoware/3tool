# Entwicklerdokumentation

## Ziel

Diese Datei beschreibt die technischen Standards für das Projekt und die
vollautomatische Qualitätsprüfung.

## Architektur (Struktur)

- `core/`: zentrale Logik (Validierung, Pfade, Konfiguration, Themes,
  Konsistenz-Checks).
- `tests/`: automatisierte Tests.
- `scripts/`: QA-Skripte für lokale Prüfungen.
- `data/`: versionierte Daten (z. B. UI-Texte und Manifestdatei).

## Manifest-Standard (JSON)

Es gibt ein versioniertes JSON-Manifest in:

- `data/manifest/v1/project_files.json`

Erzeugung:

```bash
python -m core.file_manifest --project-root . --output data/manifest/v1/project_files.json
```

Prüfung:

```bash
python -m core.file_manifest --verify
```

Das Manifest enthält pro getrackter Datei:

- relativen Pfad
- Dateigröße
- SHA256-Prüfsumme

Damit sind Änderungen transparent nachvollziehbar.

## Qualitäts- und Wartbarkeitsstandards

- Einheitliche Zeilenlänge (80 Zeichen) über `black`/`ruff`.
- Strikte Typprüfung über `mypy`.
- Reproduzierbare Tests über `pytest`.
- Abhängigkeits-Konsistenz über `core.dependency_consistency`.
- Integritätsprüfung über `core.file_manifest`.

## Vollautomatische Prüfung

`./scripts/qa.sh` führt die vollständige Prüfkette aus:

1. Syntaxprüfung (`compileall`)
2. Manifest-Integritätsprüfung
3. Linting (`ruff`)
4. Formatprüfung (`black --check`)
5. Typprüfung (`mypy`)
6. Tests (`pytest`)


## GUI-Layout-Standards (kurz)

- Dialoge nutzen skalierbare EM-Konstanten statt fixer Pixelwerte
  (abhängig von Schriftgröße und DPI).
- Mindestgrößen werden mit `minimumSize` und `QSizePolicy` abgesichert,
  damit Kern-Controls auch bei kleinen Fenstern sichtbar bleiben.
- `QSplitter` nutzt relative Gewichte über `setStretchFactor` für stabile
  Flächenverteilung zwischen Listen- und Vorschau-Bereich.
- Vorschau-Zoom basiert auf verfügbarer Fläche (`contentsRect`) statt auf
  festen Pixel-Basen; dadurch bleibt die Darstellung bei hoher Skalierung
  robust.

## Hinweise für robuste Erweiterungen

- Neue Konfigurationswerte immer zentral validieren.
- UI-Texte in `data/texts/v1/de.json` versioniert ablegen.
- Fehler stets verständlich melden und eine Lösung anbieten.
- GUI-Thread nicht blockieren; lange Jobs asynchron ausführen.

## Text-Workflow (UI-Texte zentral und austauschbar)

1. **Neuen Text nur über Schlüssel anlegen**
   - Text zuerst in `data/texts/v1/de.json` als Key ergänzen.
   - Danach denselben Key in `data/texts/v1/en.json` pflegen.
2. **Im Code immer Fallback nutzen**
   - UI-Texte in der GUI nur über `text_with_fallback(...)` oder einen Helper
     (z. B. `_ui_text`) abrufen.
   - Keine neuen harten Strings in `QMessageBox`, `setToolTip` oder
     `statusBar().showMessage` einbauen.
3. **Formatfelder stabil halten**
   - Platzhalter wie `{path}` oder `{count}` in allen Locales identisch halten.
4. **Automatisch prüfen**
   - Guard-Test: `tests/test_ui_texts.py` verhindert neue harte UI-Texte in
     `videobatch_gui.py`.
5. **Änderung validieren**
   - Pflicht: `scripts/quality_check.sh` und `pytest` ausführen.

Kurzregel: Erst JSON-Schlüssel, dann Codeverdrahtung, danach Tests.
