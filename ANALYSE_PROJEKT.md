# Projektanalyse

Dieses Dokument sammelt Hinweise zur Verbesserung des Quellcodes.

## Gefundene Probleme

- Viele Zeilen sind laenger als 79 Zeichen (Empfehlung aus *PEP8* – Styleguide fuer Python).
- Einige Funktionen nutzen mehrere Befehle in einer Zeile, was schwer zu lesen ist.
- Importzeilen fuehren mehrere Module in einer Zeile auf.

## Vorschlaege

1. `flake8` nutzen, um Warnungen Schritt fuer Schritt zu beheben.
   ```bash
   pip install flake8
   flake8 videobatch_extra.py videobatch_gui.py videobatch_launcher.py
   ```
2. Lange Zeilen aufteilen und Befehle untereinander schreiben.
   ```python
   # vorher
   if ok: do_something(); do_more()

   # besser
   if ok:
       do_something()
       do_more()
   ```
3. Importzeilen trennen, damit jede Zeile ein Modul enthaelt.
   ```python
   import sys
   import os
   ```
4. Wiederholten Code in Funktionen auslagern. Dies nennt man *Refactoring* (Umstrukturierung).

## Unvollstaendige Stellen

- `videobatch_extra.py` meldet FFmpeg-Fehler nur knapp. Eine ausfuehrlichere Meldung waere hilfreich.
- Im GUI-Teil fehlt teils eine Pruefung, ob Dateien existieren. Das sollte ergaenzt werden.

## Weiterfuehrende Tipps fuer Laien

Diese Hinweise helfen beim Einstieg und koennen direkt in einem Terminal
ausprobiert werden. Fachbegriffe stehen in Klammern und werden erklaert.

1. **Testprojekt anlegen**
   ```bash
   mkdir testprojekt
   cd testprojekt
   python3 ../videobatch_extra.py --selftest
   ```
   `mkdir` erstellt einen Ordner. Mit `cd` (change directory) wechselst du hinein.
   Der Befehl `--selftest` prueft die wichtigsten Funktionen.

2. **Programm mit Beispielaufruf starten**
   ```bash
   python3 videobatch_extra.py --img bild.jpg --aud ton.mp3 --out output
   ```
   Erscheint eine Fehlermeldung, hilft der Text **FFmpeg-Fehler** weiter.

3. **Code erneut ueberpruefen**
   ```bash
   flake8 videobatch_extra.py
   ```
   `flake8` ist ein Analysewerkzeug, das auf moegliche Tippfehler hinweist.

## Weiterfuehrende Tipps fuer Laien – Teil&nbsp;2

Diese Tipps gehen noch einen Schritt weiter und zeigen nuetzliche Befehle in
leichter Sprache. Wie zuvor stehen Fachbegriffe in Klammern und werden kurz
erklaert.

1. **Backup anlegen** (Sicherungskopie)
   ```bash
   zip -r backup.zip .
   ```
   Das Programm `zip` verpackt alle Dateien im aktuellen Ordner zu einer
   kompakten Kopie. So laesst sich der Stand leicht wiederherstellen.

2. **Projekt aktualisieren**
   ```bash
   git pull
   ```
   `git` ist eine Versionsverwaltung. Der Befehl `pull` holt die neuesten
   Aenderungen von der Quelle.

3. **Virtuelle Umgebung entfernen**
   ```bash
   deactivate
   rm -r .venv
   ```
   Mit `deactivate` verlaesst du die Umgebung. Anschliessend loescht `rm -r`
   (remove) den Ordner `.venv`. Beim naechsten Start richtet der Launcher sie
   automatisch neu ein.

## Weiterfuehrende Tipps fuer Laien – Teil 3

Auch dieser Abschnitt nutzt einfache Sprache. Die Befehle lassen sich direkt
kopieren und ausprobieren. Fachwörter stehen in Klammern und werden kurz
beschrieben.

1. **Dateien nach Datum sortieren**
   ```bash
   ls -lt
   ```
   `ls` listet Dateien. Die Option `-lt` zeigt sie nach Zeit geordnet an
   (die jünsten zuerst).

2. **Freien Speicher anzeigen**
   ```bash
   df -h
   ```
   `df` gibt eine Übersicht des Speicherplatzes aus. Mit `-h` (human readable)
   werden die Werte in leicht lesbaren Einheiten wie MB oder GB angegeben.

3. **Tool im Vollbild starten**
   ```bash
   python3 videobatch_launcher.py --fullscreen
   ```
   Einige Fenster wirken übersichtlicher im Vollbildmodus. Der Parameter
   `--fullscreen` (ganzer Bildschirm) startet das Programm entsprechend.

## Weiterfuehrende Tipps fuer Laien – Teil 4

Diese Befehle geben weiteren Einblick. Sie sind kurz erklaert und koennen
so uebernommen werden.

1. **Dateigroessen anzeigen**
   ```bash
   du -sh *
   ```
   `du` (disk usage) zeigt, wie viel Platz jede Datei benoetigt. `-h` gibt
   die Werte in MB oder GB aus.

2. **Laufende Programme auflisten**
   ```bash
   ps aux | head
   ```
   `ps aux` listet alle laufenden Prozesse. Mit `head` werden nur die ersten
   Zeilen angezeigt.

3. **Text in Dateien suchen**
   ```bash
   grep -R "Fehler" .
   ```
   `grep` sucht nach dem Wort "Fehler" in allen Dateien. `-R` bedeutet
   rekursiv (auch Unterordner werden durchsucht).

## Weiterfuehrende Tipps fuer Laien – Teil 5

Auch dieser Abschnitt verwendet einfache Sprache. Fachbegriffe werden kurz in Klammern erlaeutert.

1. **Dateien nach Groesse sortieren**
   ```bash
   ls -lS
   ```
   `ls` zeigt Dateien im aktuellen Ordner. Mit `-lS` werden sie nach der Dateigroesse sortiert.

2. **Temporäre Dateien finden**
   ```bash
   find . -name "*.tmp"
   ```
   `find` sucht in Ordnern. `*.tmp` steht fuer Dateien mit der Endung `.tmp`.

3. **Speicherbedarf pro Ordner anzeigen**
   ```bash
   du -sh ./*
   ```
`du` (disk usage) zeigt den belegten Speicher. `-h` sorgt fuer leicht lesbare Werte (MB oder GB).

## Weiterfuehrende Tipps fuer Laien – Teil 6

Auch dieser Teil nutzt einfache Sprache und zeigt nuetzliche Befehle.

1. **Ins Elternverzeichnis wechseln**
   ```bash
   cd ..
   ```
   `cd` (change directory) wechselt in einen anderen Ordner. Mit `..` geht es eins hoch.

2. **Dateiinhalt anzeigen**
   ```bash
   cat README.md
   ```
   `cat` gibt den Inhalt einer Datei direkt im Terminal aus.

3. **Zuletzt eingegebene Befehle anzeigen**
   ```bash
   history | tail
   ```
   `history` zeigt die Befehlsgeschichte. `tail` beschränkt die Ausgabe auf die letzten Zeilen.

## Weiterfuehrende Tipps fuer Laien – Teil 7

Auch dieser Teil nutzt einfache Erklaerungen.

1. **Alte Logdateien loeschen**
   ```bash
   rm *.log
   ```
   `rm` (remove) entfernt Dateien. `*.log` steht fuer alle Protokolldateien.

2. **Zeilen in einer Datei zaehlen**
   ```bash
   wc -l datei.txt
   ```
   `wc` (word count) zaehlt mit `-l` die Zeilen einer Datei.

3. **Audio in MP3 umwandeln**
   ```bash
   ffmpeg -i ton.ogg ton.mp3
   ```
   `ffmpeg` (Video-und Audio-Tool) liest `ton.ogg` und erstellt `ton.mp3`.

## Weiterfuehrende Tipps fuer Laien – Teil 8

1. **Festplattenplatz pruefen**
   ```bash
   df -h
   ```
   `df` (disk free) zeigt mit `-h` die freien und belegten Gigabytes an.

2. **FFmpeg-Ordner in den Pfad aufnehmen**
   ```bash
   export PATH="$PATH:/opt/ffmpeg/bin"
   ```
   `export` legt eine Umgebungsvariable an. So findet das Terminal das Programm.

3. **Dateirechte anpassen**
   ```bash
   chmod +x skript.sh
   ```
   `chmod` (change mode) macht eine Datei ausfuehrbar.

## Weiterfuehrende Tipps fuer Laien – Teil 9

Diese Tipps helfen beim Aufraeumen und Halten des Systems auf dem neuesten Stand. Die Befehle lassen sich direkt kopieren.

1. **Groesste Ordner finden**
   ```bash
   du -sh */ | sort -h
   ```
   `du` (disk usage) misst den Platzverbrauch. Mit `sort -h` werden die Ergebnisse nach Groesse sortiert.

2. **Laufende Prozesse bequem ansehen**
   ```bash
   ps aux | less
   ```
   `ps` zeigt alle Programme. `less` (DurchblÃ¤tterer) erlaubt bequemes Scrollen.

3. **System aktuell halten**
   ```bash
   sudo apt update && sudo apt upgrade
   ```
  `apt` ist der Paketverwalter. `update` holt neue Listen, `upgrade` installiert die Aktualisierungen.

## Weiterfuehrende Tipps fuer Laien – Teil 10

Dieser Abschnitt zeigt weitere nuetzliche Befehle in einfacher Sprache.
Wie gewohnt stehen Fachwoerter in Klammern mit kurzer Erklaerung.

1. **Versteckte Dateien anzeigen**
   ```bash
   ls -a
   ```
   `ls` (list) zeigt die Dateien im aktuellen Ordner. Mit `-a` (all) werden auch
   verborgene Dateien angezeigt.

2. **Datei verschieben oder umbenennen**
   ```bash
   mv quelle.txt ziel.txt
   ```
   `mv` (move) verschiebt eine Datei. Wenn der Zielname anders ist, wird sie
   zugleich umbenannt.

3. **Text ohne Beachtung von Gross/Kleinschreibung suchen**
   ```bash
   grep -i "wort" datei.txt
   ```
   `grep` (search) findet Zeilen, die das Wort enthalten. Die Option `-i`
   ignoriert die Schreibweise.

## Weiterfuehrende Tipps fuer Laien – Teil 11

Auch dieser Abschnitt nutzt einfache Sprache. Die Befehle lassen sich direkt
kopieren und ausprobieren.

1. **Nur Bilder anzeigen**
   ```bash
   ls *.jpg
   ```
   `ls` (list) zeigt mit `*.jpg` nur Dateien, die auf `.jpg` enden.

2. **Alle Dateien zu einem Archiv packen**
   ```bash
   tar -czf archiv.tar.gz *
   ```
   `tar` erstellt ein gepacktes Archiv. Die Optionen `-czf` bedeuten
   "komprimieren" (c), "gzip nutzen" (z) und "Dateiname folgt" (f).

3. **Laufende Python-Prozesse suchen**
   ```bash
   ps aux | grep python
   ```
   `ps aux` listet alle Prozesse. `grep` filtert hier nur Zeilen, in denen
   "python" vorkommt.

## Weiterfuehrende Tipps fuer Laien – Teil 12

Auch dieser Abschnitt enthaelt einfache Beispiele. Jede Zeile laesst sich
kopieren und im Terminal ausfuehren.

1. **Dateien zaehlen** (Anzahl bestimmen)
   ```bash
   ls | wc -l
   ```
   `wc` (word count) zaehlt hier alle Zeilen und damit die angezeigten Dateien.

2. **Leeren Ordner anlegen**
   ```bash
   mkdir neuer_ordner
   ```
   `mkdir` (make directory) erstellt einen neuen Ordner.

3. **Ordner entfernen**
   ```bash
   rmdir neuer_ordner
   ```
   `rmdir` (remove directory) loescht ihn wieder, sofern er leer ist.

## Weiterfuehrende Tipps fuer Laien – Teil 13

Auch dieser Abschnitt verwendet einfache Sprache. Alle Befehle koennen direkt kopiert werden.

1. **Letzte Zeilen einer Protokolldatei anzeigen**
   ```bash
   tail -n 20 datei.log
   ```
   `tail` (letzter Teil) zeigt mit `-n` die gewuenschte Anzahl an Zeilen von unten.

2. **Netzwerkverbindung testen**
   ```bash
   ping -c 4 example.com
   ```
   `ping` prueft die Verbindung. Die Option `-c` gibt an, wie oft das Paket gesendet wird.

3. **Grosse Dateien finden**
   ```bash
   find . -type f -size +50M
   ```
  `find` sucht Dateien. Die Angabe `+50M` bedeutet groesser als 50 Megabyte.

## Weiterfuehrende Tipps fuer Laien – Teil 14

Auch dieser Abschnitt nutzt einfache Begriffe und erklaert Fachwoerter in Klammern.

1. **Archiv entpacken**
   ```bash
   unzip archiv.zip
   ```
   `unzip` (auspacken) entlaedt den Inhalt der ZIP-Datei in den aktuellen Ordner.

2. **Dateigroessen uebersichtlich anzeigen**
   ```bash
   ls -lh
   ```
   `ls` (list) zeigt mit `-l` eine detaillierte Liste und mit `-h` (human readable) gut lesbare Groessen an.

3. **Systemauslastung beobachten**
   ```bash
   top
   ```
   `top` zeigt laufende Prozesse und deren CPU-Auslastung in Echtzeit.
