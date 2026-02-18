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
