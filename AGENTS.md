# Projekt-Richtlinien (Darstellung, Flexibilität, Responsive Design)

## Ziel und Geltungsbereich
Diese Richtlinie fokussiert ausschließlich auf:
- Darstellung (UI-Layout, visuelle Konsistenz)
- grafische Flexibilität (Themes, Kontrast, Skalierung)
- dynamische automatische Anpassbarkeit (DPI, Schriftgröße, Reflow)
- Responsive Design (verschiedene Fenstergrößen, Breakpoints, Umbruch)

Alle bisher nicht direkt dazugehörigen Regeln wurden nach `agent_old.txt` verschoben.

## Pflichtstandards für UI/UX
- Maximale Barrierefreiheit: hoher Kontrast, sichtbarer Fokus, vollständige Tastaturbedienung.
- Einheitliche Abstände, Größen, Schrift-Hierarchien und Komponentenverhalten.
- Mehrere Farbthemes mit verlässlichem Kontrastverhalten und klarer Lesbarkeit.
- Keine rein farbliche Bedeutung ohne zusätzliche textliche Erklärung.
- Dynamischer Reflow: Layout passt sich automatisch an Fenstergröße, DPI und Schrift-Skalierung an.
- Responsive Komponenten dürfen keine wichtigen Bedienelemente verdecken.

## Qualitätsvorgaben für Darstellungsänderungen
- Für sichtbare Änderungen sind automatische UI-Tests zu pflegen/ergänzen.
- Bei Änderungen an Themes/Kontrast sind Kontrast- und Lesbarkeitstests auszuführen.
- Fehlerhinweise in einfacher Sprache mit nächstem Schritt und kopierbarem Befehl.

## Wartbarkeit
- Darstellungscode modular halten (`gui/`), wiederverwendbare Hilfen zentralisieren.
- Konfiguration, variable Laufzeitdaten und Quellcode getrennt halten.
- Konsistente Benennung und einheitliche UI-Standards in allen Ansichten.

---

## PROVOWARE GLOBAL DEVELOPMENT CONTRACT

Dieser globale Kern gilt zusätzlich zu den projektspezifischen Regeln. Bei Sicherheits- oder Nachvollziehbarkeitskonflikten hat er Vorrang; lokale Regeln dürfen ihn verschärfen, nicht stillschweigend abschwächen.

- **Frozen Current Plan:** Laufenden freigegebenen Plan nicht durch neue Ideen erweitern; Neues in die nächste Iteration einordnen.
- **Conflict Gate:** Unterbrechen nur bei nachgewiesenem Konflikt mit Planvoraussetzung, Sicherheit, Ausgangs-SHA, Scope oder Invariant.
- **Single Writer:** Pro produktivem Scope nur ein autorisierter Executor; Analyse/Planung/Prüfung dürfen parallel lesen.
- **SHA + Scope:** Vor Mutation HEAD und erlaubten/verbotenen Scope prüfen; keine stillen Nebenrefactorings.
- **Evidence:** Kein PASS ohne echten Test; Evidence muss zum geprüften HEAD gehören.
- **Controlled Evidence Lab:** Echte Mutationen, Fehler-Injektion und Recovery-Tests nur in isolierten Testbereichen; Produktivdaten bleiben geschützt.
- **Next Queue:** Neue Anforderungen/Findings append-only erfassen und Beziehungen wie BLOCKS, REQUIRES, SUPERSEDES, DUPLICATE oder CONFLICTS dokumentieren.
- **Statusklarheit:** OBSERVED/SUSPECTED/REPRODUCED/CONFIRMED/DISPROVED nicht vermischen.
- **Recovery Key:** Nach Abbruch oder Agentenwechsel müssen Stand, Ziel, Frozen Plan, Scope, Findings, Gates und nächster erlaubter Schritt ohne alten Chat rekonstruierbar sein.
- **Traceability:** Requirement/Decision → Finding → Plan → Change → Test/Evidence → Gate/Checkpoint nachvollziehbar halten.
- **Negativtests:** Schutzmechanismen absichtlich gegen falschen SHA, zweiten Writer, Scope-Verstoß und unbelegtes PASS testen.
- **Sichtbarer Fortschritt:** Längere Prüfungen mit Schritt, Fortschritt, Ergebnis und Ampelstatus darstellen.

Leitsatz: **Kein Agent muss sich erinnern. Kein Agent darf raten. Keine Änderung verliert ihren Ursprung. Kein PASS existiert ohne Evidence.**
