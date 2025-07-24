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

## 5. Nur den Ton speichern
```bash
ffmpeg -i video.mp4 -vn ton.mp3
```
*`-vn`* bedeutet "ohne Video". So erhält man nur die Tonspur.

## 6. Helligkeit anpassen
```bash
ffmpeg -i clip.mp4 -vf "eq=brightness=0.1" heller.mp4
```
*`eq`* steht für "equalizer". Der Wert `0.1` macht das Bild etwas heller.

## 7. Schrift und Farben im Tool

- Im Menü **Ansicht** kann man die Schriftgröße verändern.
- Unter **Theme** hilft das Design **Kontrast** bei schwächerem Sehen.

Weitere Tipps findest du in `ANLEITUNG_GESAMT.md`.

## 8. Kurzes Stück ausschneiden
```bash
ffmpeg -ss 00:00:10 -i original.mp4 -t 00:00:20 -c copy kurz.mp4
```
*`-ss`* gibt die Startzeit an. *`-t`* bestimmt die Länge des Ausschnitts.

Mit dem Knopf **Öffnen** im Hauptfenster wird der Ausgabeordner angezeigt.
