# Projekt-Richtlinien

- Bei jeder Änderung muss mindestens eine offene Aufgabe aus `todo.txt` vollständig erledigt werden.
- Abgeschlossene Aufgaben werden in `todo.txt` abgehakt und im Commit-Kommentar erwähnt.
- Jede Erledigung wird zusätzlich im `ereignislog.txt` protokolliert.
- In jeder Iteration wird mindestens eine Aufgabe erledigt.

## Entwicklungsdisziplin (sicher & effizient)

- Vor jeder Änderung: kurze Ist-Analyse, Risiko-Check und Plan mit maximal 5 Schritten.
- Jede Funktion validiert Eingaben und bestätigt Erfolg/Ausgabe eindeutig im Log.
- Keine Blockierung des GUI-Threads; lange Aufgaben immer asynchron (Thread/Worker).
- Defensive Programmierung: sichere Defaults, klare Fehlermeldungen, Recovery-Hinweise.
- Debug-/Logging-Modus mit laienverständlichen Lösungsvorschlägen pflegen.
- Nach Änderungen immer automatisierte Checks ausführen (`scripts/quality_check.sh`, `pytest`).
- Bei Fehlern zuerst automatische Reparaturpfade nutzen, dann nachvollziehbares Nutzerfeedback.

## Architektur- und Wartbarkeitsstandard

- Tool-Logik strikt trennen in: `core/` (Logik), GUI, Daten (`data/`), Skripte (`scripts/`).
- Variable Dateien und Konfiguration getrennt halten (Config ≠ Code ≠ Nutzdaten).
- Wiederverwendbare Hilfsfunktionen in `core/` zentralisieren, keine duplizierte Logik.
- Einheitliche Benennung, einheitliche Abstände/Größen, konsistente UI-Elemente.

## Barrierefreiheit & Layout Best Practices

- Maximale Barrierefreiheit: hoher Kontrast, klare Fokusmarkierung, Tastaturbedienbarkeit.
- Mehrere Themes bereitstellen und Kontrastverhalten regelmäßig testen.
- Große, klare Dashboard-Zahlen und direkt sichtbarer Fortschritt.
- Verständliche Sprache für Laien; Fachwort nur mit kurzer Erklärung in Klammern.

## Präventive Fehlervermeidung & Self-Repair

- Startroutine prüft automatisch Abhängigkeiten und gibt verständliches Nutzerfeedback.
- Fehlerfälle mit Fallback-Strategien absichern (z. B. Ersatzmedien bei ungültigen Dateien).
- Selbstreparatur-Hinweise dokumentieren und bei Bedarf automatisch anwenden.

## Qualitäts-Setup (vollautomatisch)

- Sinnvolle automatische Tests pflegen und erweitern.
- Automatisches Code-Formatting und Qualitätsprüfungen in Skripten bündeln.
- Reproduzierbare Builds und klare Dokumentation sicherstellen.

## Arbeitspakete (schrittweise)

1. Ist-Analyse & Planung
   - Code, Struktur, AGENTS-Dateien prüfen.
   - Schwachstellenliste + Kurz-Roadmap erstellen.
2. Architektur ordnen
   - Module logisch trennen (Core/Services/UI/CLI/Data).
   - Globale Zustände kapseln.
   - Wiederholte Utilities zusammenführen.
3. Qualitäts-Setup
   - Tests, Linting, Formatierung und Auto-Checks stabilisieren.
