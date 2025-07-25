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
- Durch die neuen Überschriften findest du Dateien, Einstellungen, Tabelle und Hilfe leichter.
- Mit **Schrift Reset** stellst du die Standardgröße wieder her.

Weitere Tipps findest du in `ANLEITUNG_GESAMT.md`.

## 8. Kurzes Stück ausschneiden
```bash
ffmpeg -ss 00:00:10 -i original.mp4 -t 00:00:20 -c copy kurz.mp4
```
*`-ss`* gibt die Startzeit an. *`-t`* bestimmt die Länge des Ausschnitts.

Mit dem Knopf **Öffnen** im Hauptfenster wird der Ausgabeordner angezeigt.

## 9. Favoriten nutzen

- In der **Bilder**-Liste mit der rechten Maustaste auf ein Bild klicken und
  **Zu Favoriten** wählen.
- Wechsle zum Tab **Favoriten**. Dort findest du das gespeicherte Bild.
- Ziehe das Bild per Drag&Drop in den Arbeitsbereich, um es sofort zu verwenden.
- Im unteren Log-Bereich erscheinen alle Schritte als Meldung.

## 10. Kontrast-Theme einschalten
- Öffne das Menü **Theme** oben im Fenster.
- Wähle dort **Kontrast**. Dadurch erscheinen gelbe Buchstaben auf schwarzem Hintergrund.
- Diese Ansicht hilft, wenn die Augen nicht mehr so fit sind.

## 11. Video leiser machen
```bash
ffmpeg -i eingang.mp4 -filter:a "volume=0.5" leiser.mp4
```
*`volume`* (Lautstärke) mit dem Wert `0.5` reduziert die Lautstärke auf fünfzig Prozent.
## 12. Video drehen
```bash
ffmpeg -i eingang.mp4 -vf "transpose=1" gedreht.mp4
```
*`transpose`* (drehen) richtet das Bild neu aus. Der Wert `1` steht für eine 90°-Drehung.

## 13. Größe ändern
```bash
ffmpeg -i eingang.mp4 -vf scale=1280:720 kleiner.mp4
```
`scale` (skalieren) passt Breite und Höhe an.

## 14. Mehrere Bilderordner koppeln
Wenn du für jede Tonspur einen eigenen Bilderordner hast, kannst du das
automatisch zuordnen lassen:

1. Wähle im Tab **Bilder** alle gewünschten Ordner aus.
2. Füge im Tab **Audios** die passenden Tondateien hinzu – in der gleichen Reihenfolge.
3. Klicke auf **Auto-Paaren**.

Das Tool erstellt dann für jeden Ordner eine eigene Slideshow.

## 15. Rand entfernen
```bash
ffmpeg -i eingang.mp4 -vf "crop=1280:720:0:60" ohne_rand.mp4
```
`crop` (beschneiden) löscht oben und unten je 60 Pixel.

## 16. Geschwindigkeit ändern
```bash
ffmpeg -i eingang.mp4 -filter:v "setpts=0.5*PTS" schneller.mp4
```
`setpts` passt die Abspielzeit an. Hier läuft das Video doppelt so schnell.

## 17. Metadaten anzeigen
```bash
ffprobe -v quiet -show_format -show_streams eingang.mp4
```
`ffprobe` ist ein Analyse-Werkzeug (Hilfsprogramm), das Informationen wie Auflösung und Kodierung ausgibt.

## 18. Modernes Theme nutzen

- Öffne das Menü **Theme** im Hauptfenster.
- Wähle **Modern**. Dieses Design bietet gute Lesbarkeit und angenehme Farben.

## 19. Hilfe-Bereich ein- oder ausblenden

- Im Menü **Ansicht** gibt es den neuen Punkt **Hilfe-Bereich**.
- Nimm den Haken weg, wenn du mehr Platz brauchst.
- Setze ihn wieder, um die kurzen Hinweise anzuzeigen.

## 20. Mehrere Audios mit einem Bild

- Im Tab **Bilder** ein einzelnes Bild auswählen.
- Unter **Audios** mehrere Tondateien hinzufügen.
- Bei **Modus** die Option **Mehrere Audios, 1 Bild** wählen.
- Auf **Auto-Paaren** klicken und danach **START** drücken.

```bash
python3 videobatch_extra.py --mode multi-audio --img bild.jpg --aud ton1.mp3 ton2.mp3 --out output
```
`multi-audio` nutzt das gleiche Bild für alle Audios.

## 21. Kontrast stärker machen

```bash
ffmpeg -i eingang.mp4 -vf "eq=contrast=1.5" kontrast.mp4
```
`eq` (Equalizer) passt Helligkeit und Kontrast an. Der Wert `1.5` sorgt für ein satteres Bild.

## 22. Video in Schleife abspielen
```bash
ffmpeg -stream_loop -1 -i clip.mp4 -c copy loop.mp4
```
`stream_loop -1` bedeutet, dass das Video immer wiederholt wird. Es entsteht eine Endlosschleife.

## 23. Logo einfügen
```bash
ffmpeg -i video.mp4 -i logo.png -filter_complex "overlay=10:10" mit_logo.mp4
```
`overlay` (Überlagerung) setzt das Logo 10 Pixel vom linken und oberen Rand ins Bild.

## 24. Fenster flexibel anpassen

- Klappe links die **Sidebar** auf oder zu über das Menü **Ansicht**.
- Ziehe die Trennleiste ("Splitter") zwischen Raster und Log, um die Höhen zu ändern.

## 25. Seitenleiste schnell ausblenden

- Öffne das Menü **Ansicht**.
- Setze oder entferne den Haken bei **Sidebar**.
