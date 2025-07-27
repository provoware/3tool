# Projekt-Richtlinien

- Bei jeder Änderung muss mindestens eine offene Aufgabe aus `todo.txt` vollständig erledigt werden.
- Abgeschlossene Aufgaben werden in `todo.txt` abgehakt und im Commit-Kommentar erwähnt.
- Jede Erledigung wird zusätzlich im `ereignislog.txt` protokolliert.
- In jeder Iteration wird mindestens eine Aufgabe erledigt von diesen punkten perfekt ohne auslassungen erledigt
Aufgabenanweisung für den Agenten (Codex) – kompakt & stichpunktartig

Ziel:
Projekt vollständig konsolidieren, technisch sauber, laientauglich bedienbar, moderne GUI, konsistente AGENTS-Dateien, automatisierbare Qualitätssicherung.

Leitplanken
Keine Blockierung des GUI-Threads.

Einheitliche Sprache & Struktur.

Reproduzierbare Builds, klare Doku.

AGENTS-/Automation-Dateien konsistent, kommentiert, funktionsfähig.

Arbeitspakete (schrittweise)
Ist-Analyse & Planung

Code, Struktur, AGENTS-Dateien prüfen.

Schwachstellenliste + Kurz-Roadmap erstellen.

Feature-Branch anlegen.

Architektur ordnen

Module logisch trennen (Core/Services/UI/CLI/Data).

Globale Zustände kapseln.

Wiederholte Utilities zusammenführen.

Qualitäts-Setup

Formatter, Linter, Typprüfung einrichten.

Basis-Testgerüst (Unit, GUI-Smoke) aufsetzen.

Coverage- & Audit-Tools hinzufügen.

Job-/Service-Layer

Job-Model (Status, Progress, Fehler).

Service-Klassen für Encoding/Pairing.

Asynchrone Ausführung + Abbruch/Retry-Hooks.

GUI-Modernisierung

Styles/Themes extern verwalten.

Fortschrittsanzeigen, Fehlermeldungs-Dialoge.

Settings & Projektdateien persistieren.

Onboarding-/Hilfeflächen für Laien.

CLI & Dry-Run

Minimaler CLI-Einstiegspunkt.

Testlauf-Option ohne Rendern.

CI/CD & Releases

Pipeline für Lint/Tests/Builds.

Artefakte für Hauptplattformen erzeugen.

Abhängigkeitschecks automatisieren.

Doku & Onboarding

Kurzanleitung (Start in <10 Min).

Entwickler-Doku (Contribute, Build, Tests).

Changelog & Versionierung etablieren.

AGENTS-Dateien korrigieren

Rollen/Prompts vereinheitlichen.

Variablen/Parameter klar dokumentieren.

Validierung/Tests der Agent-Workflows.

Abschluss & Übergabe

Definition-of-Done prüfen (Tests grün, Lint sauber).

Release taggen, Doku finalisieren.

Backlog offener Verbesserungen erfassen.


