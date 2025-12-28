# Einfache Anleitung

Diese Anleitung richtet sich an Anfaenger und erklaert jeden Schritt.

1. **Datei herunterladen**
   - Klicke oben rechts auf "Code" und waehle "Download ZIP".
   - Entpacke die ZIP-Datei.

2. **Terminal oeffnen** (Befehlseingabe-Fenster).
   - Navigiere in den Ordner mit den entpackten Dateien.
   - Beispiel (unter Linux/macOS):
     ```bash
     cd ~/Downloads/VideoBatchTool
     ```

3. **Virtuelle Umgebung** (isolierter Arbeitsbereich fuer Python) anlegen:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   Danach steht in der Eingabezeile meist ein Praefix wie `(venv)`.

4. **Abhaengigkeiten** (benoetigte Bibliotheken) installieren:
   ```bash
   pip install -r requirements.txt
   ```

5. **Programm starten**:
   ```bash
   python3 videobatch_launcher.py
   ```
   Der Launcher prueft, ob alles korrekt eingerichtet ist und startet dann die grafische Oberflaeche (GUI).

6. **Selbsttest** (funktioniert ohne GUI):
   ```bash
   python3 videobatch_extra.py --selftest
   ```
   Bei Erfolg erscheint die Meldung `Selftests OK`.
7. **Qualitaets-Check** (automatische Pruefung von Code, Format und Tests):
   ```bash
   bash scripts/qa.sh
   ```
   Das Skript nutzt:
   - **ruff** (Linter = Code-Pruefer)
   - **black** (Formatter = automatische Formatierung)
   - **mypy** (Typpruefung)
   - **pytest** (Testlauf)
8. **Log-Bereich**:
   Unten im Fenster laufen die Meldungen mit. Im Menü "Hilfe" kannst du mit "Logdatei öffnen" alles nachlesen.
9. **Übersicht**:
   Die Dateien, Einstellungen, Tabelle und Hilfe sind jetzt durch klare Überschriften getrennt.
10. **Favoriten nutzen**:
   - In der Liste **Bilder** mit der rechten Maustaste auf ein Bild klicken und **Zu Favoriten** wählen.
   - Wechsle zum Tab **Favoriten**. Dort kannst du das Bild per Drag&Drop in den Arbeitsbereich ziehen.
   - Unter **Ansicht** lässt sich zudem die Schriftgröße vergrößern, was für sehschwache Menschen hilfreich ist.
   - Über das Menü **Theme** kann ein kontrastreiches Farbschema gewählt werden.
Weitere Fragen werden in `README.md` beantwortet.
