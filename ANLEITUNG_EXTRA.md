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

## 6. Video drehen
```bash
ffmpeg -i eingang.mp4 -vf "transpose=1" gedreht.mp4
```
*`transpose`* dreht das Bild. Der Wert `1` bedeutet 90 Grad im Uhrzeigersinn.

## 7. Video spiegeln
```bash
ffmpeg -i eingang.mp4 -vf "hflip" spiegel.mp4
```
*`hflip`* spiegelt das Video horizontal wie in einem Spiegel.

## 8. Logo in Ecke einblenden
```bash
ffmpeg -i film.mp4 -i logo.png -filter_complex "overlay=10:10" mit_logo.mp4
```
*`overlay`* legt ein Bild über das Video. `10:10` gibt die Position in Pixeln an.

## 9. Untertitel einbrennen
```bash
ffmpeg -i film.mp4 -vf "subtitles=text.srt" film_ut.mp4
```
*`subtitles`* mischt die Datei `text.srt` direkt in das Video.

Weitere Hinweise findest du in `ANLEITUNG_GESAMT.md`.

