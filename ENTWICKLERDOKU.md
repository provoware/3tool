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

## Hinweise für robuste Erweiterungen

- Neue Konfigurationswerte immer zentral validieren.
- UI-Texte in `data/texts/v1/de.json` versioniert ablegen.
- Fehler stets verständlich melden und eine Lösung anbieten.
- GUI-Thread nicht blockieren; lange Jobs asynchron ausführen.
