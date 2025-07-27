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
