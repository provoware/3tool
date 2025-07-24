# Weitere Laien-Beispiele

Diese Sammlung enthaelt einfache Befehle fuer **ffmpeg**. Die Sprache ist bewusst simpel. Fachbegriffe stehen in Klammern und werden kurz erklaert.

## 1. Video in Ton umwandeln
```bash
ffmpeg -i video.mp4 -vn -acodec copy ton.mp3
```
*`-vn`* bedeutet "kein Video" (Videoanteil weglassen). *`acodec copy`* uebernimmt den vorhandenen Audiocodec unveraendert.

## 2. Mehrere Videos verbinden
```bash
ffmpeg -f concat -safe 0 -i liste.txt -c copy gesamt.mp4
```
Die Datei `liste.txt` listet alle Einzelvideos. *`concat`* (verkettung) fuegt sie ohne Neuberechnung zusammen.

## 3. Text einblenden
```bash
ffmpeg -i input.mp4 -vf "drawtext=text='Hallo':x=10:y=H-th-10:fontsize=24:fontcolor=white" mit_text.mp4
```
*`drawtext`* fuegt einen Schriftzug ein. *`x`* und *`y`* bestimmen die Position.

## 4. Geschwindigkeit halbieren
```bash
ffmpeg -i input.mp4 -filter:v "setpts=2.0*PTS" langsam.mp4
```
*`setpts`* steuert die Bildwiedergabezeit (hier doppelt so lang = halb so schnell).

## 5. Video als GIF speichern
```bash
ffmpeg -i clip.mp4 -vf "fps=10,scale=320:-1" -gifflags -transdiff gif_out.gif
```
*`fps`* legt die Bildrate (frames per second) fest, *`scale`* aendert die Groesse. *`-gifflags -transdiff`* optimiert die Dateigroesse.

Weitere Hinweise findest du in `ANLEITUNG_GESAMT.md`.

