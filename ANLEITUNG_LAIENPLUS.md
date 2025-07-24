# Zusätzliche Laien-Tipps

Dies ist eine kleine Sammlung einfacher Befehle ("commands"),
besonders für Einsteiger.
Fachbegriffe stehen in Klammern und werden erklärt.

## 1. Audio in Video einbetten
```bash
ffmpeg -loop 1 -i bild.jpg -i ton.mp3 -shortest -c:v libx264 -c:a aac video.mp4
```
*`-loop 1`* zeigt das Bild dauerhaft. *`-shortest`* beendet das Video,
wenn der Ton fertig ist.

## 2. Bilderstapel in Video verwandeln
```bash
ffmpeg -framerate 1 -pattern_type glob -i 'fotos/*.jpg' bildershow.mp4
```
*`framerate`* (Bildrate) legt fest, wie viele Bilder pro Sekunde erscheinen.

## 3. Einzelbilder aus Video speichern
```bash
ffmpeg -i film.mp4 bild_%03d.png
```
Dadurch entstehen Dateien wie `bild_001.png`.

## 4. Video lauter machen
```bash
ffmpeg -i eingang.mp4 -filter:a "volume=1.5" lauter.mp4
```
*`volume`* bestimmt die Lautstärke (1.5 = 150 Prozent).

Weitere Tipps findest du in `ANLEITUNG_GESAMT.md`.

## 5. Helligkeit anpassen
```bash
ffmpeg -i eingang.mp4 -vf "eq=brightness=0.1" heller.mp4
```
*`eq`* steht für "equalizer" (Bildkorrektur). *`brightness`* erhöht die Helligkeit.

## 6. Sanfte Einblendung am Anfang
```bash
ffmpeg -i clip.mp4 -vf "fade=t=in:st=0:d=2" -af "afade=t=in:st=0:d=2" startfade.mp4
```
*`fade`* erstellt eine Ein- oder Ausblendung. *`st`* ist der Startzeitpunkt, *`d`* die Dauer in Sekunden.


## 7. Tonspur entfernen
```bash
ffmpeg -i eingang.mp4 -an stumm.mp4
```
*`-an`* bedeutet "Audio none" und sorgt dafür, dass keine Tonspur im Ergebnis steckt.

## 8. Kurzen Ausschnitt speichern
```bash
ffmpeg -i film.mp4 -ss 00:00:10 -t 5 ausschnitt.mp4
```
*`-ss`* springt zur Startzeit, *`-t`* legt die Dauer in Sekunden fest.

## 9. Auflösung verkleinern
```bash
ffmpeg -i gross.mp4 -vf "scale=1280:720" kleiner.mp4
```
*`scale`* (Skalierung) passt Breite und Höhe an, hier auf 1280x720.

