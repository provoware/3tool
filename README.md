# VideoBatchTool

Dieses Projekt erstellt aus Bildern und Audiodateien einfache Videos im MP4-Format. Die grafische Oberflaeche (GUI) hilft beim Paaren der Dateien und beim Starten der Verarbeitung.

## Voraussetzungen

* Python 3.10 oder neuer
* `ffmpeg` und `ffprobe` muessen im Systempfad vorhanden sein
* Benötigte Pakete: PySide6, Pillow, ffmpeg-python (siehe requirements.txt)

Die benoetigten Python-Pakete stehen in `requirements.txt`.

## Schnellstart

1. Python-Abhaengigkeiten installieren:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Das Tool starten:
   ```bash
   python3 videobatch_launcher.py
   ```
   Der Launcher legt bei Bedarf automatisch ein virtuelles Umfeld ("virtual environment") an und installiert die Pakete.
   Bist du bereits in einer eigenen Umgebung, erkennt der Launcher dies und nutzt dein aktuelles Python.
3. Alternativ kann das Beispielskript `setup.sh` alles in einem Durchlauf erledigen. Ein Muster steht in `setup-sh.txt`.

### Start mit Hilfefenster

Beim ersten Start erscheint ein kleines Setup-Fenster. Es prüft, ob alle
benötigten Pakete und `ffmpeg` vorhanden sind. Über die Schaltfläche
**Installieren / Reparieren** lässt sich alles automatisch einrichten.
Mit dem Parameter `--help` zeigt der Launcher alle verfügbaren Optionen an:

```bash
python3 videobatch_launcher.py --help
```

Eine ausfuehrliche Anleitung mit allen Tipps steht in `ANLEITUNG_GESAMT.md`.
Weitere einfache Beispiele bietet `ANLEITUNG_LAIENPLUS.md`.
Im Abschnitt "Weiterführende Befehle" von `ANLEITUNG_GESAMT.md` finden sich
zusätzliche Kommandos für neugierige Einsteiger.
Weitere Beispiele stehen in `ANLEITUNG_EXTRA.md`.
Noch mehr Befehle zeigt `ANLEITUNG_WEITERE_TIPPS.md`.

## Wo liegen meine Einstellungen?

Die Einstellungen (Konfiguration) liegen in einem festen Ordner:

* **Konfigurationsordner (Ordner fuer Einstellungen):** `~/.videobatchtool/config/`
* **Einstellungsdatei (INI-Datei):** `~/.videobatchtool/config/settings.ini`

Die Logdateien (Protokolle) bleiben wie gehabt hier:

* **Log-Ordner (Protokolle):** `~/.videobatchtool/logs/`

In der Oberflaeche siehst du den Log-Pfad direkt im Protokollbereich unten.

## Neues in der Oberfläche

- **Favoriten** – Bilder lassen sich per Rechtsklick zu einer Favoritenliste hinzufügen. Im Tab "Favoriten" können sie per Drag&Drop in den Arbeitsbereich gezogen werden.
- **Farbschemata (Themes = Designfarben)** – über das Menü "Farbschema" stehen sieben unterschiedliche Farbkombinationen bereit. Neu ist das freundliche Design "Modern". Das Farbschema "Kontrast" bietet weiterhin hohe Lesbarkeit.
- **Schriftgröße** – im Menü "Ansicht" lässt sich die Schrift stufenweise anpassen.
- **Log-Anzeige** – unten im Fenster erscheinen alle Aktionen sofort als Text.
- **Überschriften** – jede Sektion besitzt nun einen klaren Titel, damit man sich leichter zurechtfindet.
- **Hilfe-Bereich ausblenden** – über "Ansicht" lässt sich der rechte Hilfeblock
  ein- oder ausblenden.
- **Log-Bereich ausblenden** – im gleichen Menü kann man den unteren Protokollbereich verstecken.
- **Einklappbare Sidebar** – links zeigen die Dateilisten eine Seitenleiste, die sich ein- oder ausblenden lässt.
- **Sidebar-Menu** – über "Ansicht" lässt sich die Seitenleiste jederzeit ein- oder ausschalten.
- **Flexibles 3×3 Raster** – mittig gibt es ein 3×3 Panelraster. Eine Ziehleiste ("Splitter") regelt die Höhe des Logs.
- **Ordner-Prüfung** – vor dem Start wird geprüft, ob der Ausgabeordner vorhanden und beschreibbar ist.
- **Launcher-Reparatur** – falls die Umgebung fehlt, legt der Launcher sie an und nutzt notfalls das aktuelle Python.
- **Fehlermeldungen** – auftretende Fehler werden nun abgefangen und verständlich gemeldet. Details stehen im Logfile (Protokolldatei).
- **Hintergrund-Verarbeitung** – das Kodieren läuft jetzt in einem eigenen Thread (Hintergrundprozess), so bleibt die Oberfläche flüssig.

Unterstuetzte Modi:
* **Standard** – ein Bild pro Audio
* **Slideshow** – ganzer Bilder-Ordner fuer jedes Audio
* **Video + Audio** – vorhandenes Video mit neuer Tonspur
* **Mehrere Audios, ein Bild** – gleiches Bild fuer viele Audiodateien
* **Slideshow mit mehreren Ordnern** – mehrere Bildordner lassen sich der Reihe nach mit den passenden Audios koppeln.
  Ordner im Tab **Bilder** hinzufügen, Audios auswählen und **Auto-Paaren** klicken.
Weitere Erklaerungen fuer Einsteiger finden sich in `ANLEITUNG_EINSTEIGER.md`.
Zusätzliche Tipps stehen in `ANLEITUNG_TIPPS.md`.

## Bedienhilfen

- Im Menü "Ansicht" kann die Schriftgröße verändert werden. Mehrfach auf "+" klicken vergrößert die Schrift.
- Unter "Farbschema" gibt es ein besonders kontrastreiches Design namens "Kontrast". Daneben steht das neue Farbschema "Modern" mit frischen Farben bereit.
- Im unteren Fensterbereich läuft ein Protokoll ("Log") mit.
- Über "Ansicht → Log-Bereich" kann diese Anzeige ausgeblendet werden.
- Über **Optionen → Debug-Log** lassen sich zusätzliche Meldungen einschalten.
- Wer lieber mit dem Terminal arbeitet, startet das Programm mit `--debug` und
  sieht dort mehr Hinweise.
- Wenn etwas schlecht zu erkennen ist, nutze das Farbschema "Kontrast" oder vergrößere die Schrift über "Ansicht".
- Bilder lassen sich als Favoriten speichern und später per Drag&Drop nutzen.
- Wenn du das Fenster größer oder kleiner ziehst, ordnen sich alle Elemente
  automatisch neu an. Auch die Trennleisten lassen sich flexibel verschieben.

## Hilfe-Fenster
Im Menü **Hilfe** gibt es den Punkt **Kurzanleitung**. Ein kleines Fenster zeigt dort die wichtigsten Schritte. Es lässt sich jederzeit öffnen.

## Tipps für ältere Nutzer

- Wähle unter "Farbschema" den Eintrag **Kontrast**, wenn Texte schwer zu lesen sind.
- Über "Ansicht → Schriftgröße" lässt sich die Schrift schnell vergrößern.
- Drücke **F11** für den Vollbildmodus. Alle Elemente werden größer dargestellt.
- Die Hilfe erreichst du jederzeit über **Hilfe → Kurzanleitung** oder die Taste **F1**.

## Barrierefreiheit

Diese Tipps erleichtern die Bedienung für alle Nutzenden:

- Unter **Ansicht → Schrift +** lässt sich die Schriftgröße jederzeit erhöhen.
- Das Farbschema **Kontrast** bietet besonders hohe Lesbarkeit bei wenig Licht.
- Viele Funktionen sind auch per Tastatur erreichbar, zum Beispiel **F1** für die Hilfe.
- Alle Bedienelemente besitzen einen klaren "AccessibleName",
  damit Screenreader die Bezeichnungen vorlesen können.

## Zusaetzlich

* Die Datei `videobatch_extra.py` enthaelt eine Kommandozeilenversion. Mit `--selftest` lassen sich einfache Tests ausfuehren.
* In `0000-testall` liegt ein Beispielskript, um Prueftools wie `flake8` oder `black` einzurichten.
* Ereignisse und Aenderungen werden in `ereignislog.txt` festgehalten.

* Neue Beispiele für Fade und Weichzeichnen stehen in `ANLEITUNG_WEITERE_TIPPS.md`.
* Ein weiteres Beispiel zum Erhöhen des Kontrasts findest du in `ANLEITUNG_TIPPS.md`.
Weitere Hinweise finden sich in den Kommentaren der Python-Dateien.

## Fehleranalyse und Optimierung

Mit dem Programm `flake8` laesst sich der Quellcode (Text des Programms) auf Fehler und Stil-Regeln (PEP8) pruefen.
```bash
pip install flake8
flake8 videobatch_extra.py videobatch_gui.py videobatch_launcher.py
```
Erscheinen Meldungen, sollte man die Zeilen pruefen.

Als Zusatz hilft der Selbsttest:
```bash
python3 videobatch_extra.py --selftest
```

## Release-Vorbereitung

Vor der Veröffentlichung ("Release") sollten alle Funktionen noch einmal getestet werden.
Gehe die Datei `todo.txt` durch und prüfe, ob überall `[x]` steht.
Für das finale Paket empfiehlt sich folgendes Vorgehen:

1. **Abhängigkeiten ("Dependencies") prüfen**:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```
2. **Syntax-Check ("Syntax check")**:
   ```bash
   python -m compileall -q .
   ```
3. **Linting ("Stil- und Regelprüfung")**:
   ```bash
   python -m ruff check .
   ```
4. **Typprüfung ("Type check")**:
   ```bash
   mypy .
   ```
5. **Automatische Tests ausführen**:
   ```bash
   python3 -m pytest
   ```
   Optionaler Zusatztest:
   ```bash
   python3 videobatch_extra.py --selftest
   ```
6. **Projekt sauber verpacken** (zum Beispiel als ZIP-Datei):
   ```bash
   zip -r videobatchtool.zip .
   ```
7. **Ereignislog sichern**: Die Datei `ereignislog.txt` dokumentiert alle Änderungen.

## Backup erstellen

Vor größeren Änderungen lohnt sich eine Sicherungskopie:
```bash
zip -r backup.zip .
```
Der Befehl `zip` fasst alle Dateien zu einem Archiv zusammen. So lässt sich der
aktuelle Stand leicht wiederherstellen.

Damit ist das Tool bereit für den Upload oder die Weitergabe.

## Weitere Optimierungen

Auch nach den Tests laesst sich noch Feinschliff vornehmen:

* **Pakete aktualisieren**
  ```bash
  pip list --outdated
  pip install -U paketname
  ```
  Damit bleiben alle Bibliotheken auf dem neuesten Stand.

* **Quellcode formatieren**
  ```bash
  black videobatch_extra.py
  ```
  `black` ordnet Einrueckungen und Zeilenumbrueche automatisch.

* **Alte Logdateien entfernen**
  ```bash
  rm *.log
  ```
  `rm` (remove) loescht alle Dateien mit der Endung `.log`.

* **Festplattenplatz pruefen**
  ```bash
  df -h
  ```
  `df` (disk free) zeigt den freien Speicherplatz an.

* **FFmpeg-Pfad setzen**
  ```bash
  export PATH="$PATH:/opt/ffmpeg/bin"
  ```
  `export` erweitert eine Umgebungsvariable, damit das Terminal ffmpeg findet.

* **Dateirechte setzen**
  ```bash
  chmod +x skript.sh
  ```
  `chmod` (change mode) macht eine Datei ausfuehrbar.

* **Groesste Ordner finden**
  ```bash
  du -sh */ | sort -h
  ```
  `du` (disk usage) zeigt den Platzbedarf. `sort -h` sortiert nach Groesse.

* **System aktualisieren**
  ```bash
  sudo apt update && sudo apt upgrade
  ```
  `apt` ist der Paketverwalter. `update` und `upgrade` halten das System aktuell.

* **Versteckte Dateien anzeigen**
  ```bash
  ls -a
  ```
  `ls` (list) zeigt mit `-a` (all) auch verborgene Dateien.

* **Nur Bilder auflisten**
  ```bash
  ls *.jpg
  ```
  Zeigt nur Dateien mit der Endung `.jpg` an.

* **Archiv erstellen**
  ```bash
  tar -czf archiv.tar.gz *
  ```
  `tar` (tape archive) sammelt alle Dateien in einem gepackten Archiv.

* **Text in Dateien suchen**
  ```bash
  grep -i "wort" datei.txt
  ```
  `grep` (search) findet das Wort unabhaengig von Gross- und Kleinschreibung.

* **Dateien zaehlen**
  ```bash
  ls | wc -l
  ```
  `wc` (word count) ermittelt die Anzahl gelisteter Dateien.

* **Neuen Ordner anlegen und entfernen**
  ```bash
  mkdir neuer_ordner
  rmdir neuer_ordner
  ```
  `mkdir` (make directory) erstellt einen Ordner. `rmdir` (remove directory)
  loescht ihn wieder, wenn er leer ist.

* **Fenstergroesse testen**
  Ziehe das Hauptfenster mit der Maus groesser oder kleiner.
  Alle Bereiche passen sich automatisch an, damit nichts verdeckt wird.

Eine komplette Anleitung mit allen Befehlen findest du in `ANLEITUNG_GESAMT.md`.

* **Speicherauslastung pruefen**
  ```bash
  free -h
  ```
  `free` zeigt den Arbeitsspeicher (RAM) an. Die Option `-h` liefert gut lesbare Werte.

* **Mehrere Dateien umbenennen**
  ```bash
  rename s/.txt/.bak/ *.txt
  ```
  `rename` aendert Dateiendungen in einem Schritt.

* **Offene Netzwerkports anzeigen**
  ```bash
  ss -tulpn
  ```
  `ss` (socket statistics) listet aktive Ports und Programme.
* **Laufende Prozesse ansehen**
  ```bash
  top -n 1
  ```
  `top` zeigt die aktiven Programme (Prozesse). Mit `-n 1` beendet sich die Anzeige nach einer Liste.

* **Kernel-Version anzeigen**
  ```bash
  uname -r
  ```
  `uname` (unix name) gibt die Version des Betriebssystemkerns (Kernel) aus.

* **Datei herunterladen**
  ```bash
  wget https://beispiel.de/datei.zip
  ```
  `wget` (web get) speichert eine Datei aus dem Internet.

* **Pruefsumme kontrollieren**
  ```bash
  sha256sum datei.zip
  ```
  `sha256sum` erstellt eine digitale Pruefsumme, um die Datei zu ueberpruefen.
