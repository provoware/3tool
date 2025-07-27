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
