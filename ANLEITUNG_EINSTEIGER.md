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

Weitere Fragen werden in `README.md` beantwortet.
