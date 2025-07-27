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

## 26. Video ohne Ton speichern

Manchmal reicht das Bild allein. So erzeugst du ein stummes Video:

```bash
ffmpeg -i eingang.mp4 -an ohne_ton.mp4
```
*`-an`* (Audio None, also ohne Ton) entfernt die Tonspur, das Video bleibt erhalten.

## 27. Untertitel einbinden

Wenn du eine Untertiteldatei hast, kannst du sie so in das Video schreiben:

```bash
ffmpeg -i video.mp4 -i text.srt -c:v copy -c:a copy -c:s mov_text video_mit_untertitel.mp4
```
*`mov_text`* (MP4-Untertitel) speichert die Texte direkt in der Datei.

## 28. Wasserzeichen einblenden

Ein kleines Logo oder ein Schriftzug kann dein Video schützen. So fügst du ihn ein:

```bash
ffmpeg -i video.mp4 -i wasserzeichen.png -filter_complex "overlay=W-w-10:H-h-10" video_mit_wz.mp4
```
*`overlay`* (Überlagerung) setzt das Wasserzeichen zehn Pixel vom unteren und rechten Rand.

## 29. Log-Datei prüfen bei Fehlern

Falls das Programm nicht startet oder eine rote Meldung erscheint, lohnt sich ein Blick in die Protokolldatei ("Log"). Damit öffnest du die neueste Datei:

```bash
nano ~/.videobatchtool/logs/$(ls -t ~/.videobatchtool/logs | head -n 1)
```

`nano` ist ein einfacher Texteditor. Die Log-Datei verrät oft die Ursache des Problems.

## 30. Zwei Tonspuren mischen
```bash
ffmpeg -i sprache.mp3 -i musik.mp3 -filter_complex "[1:a]volume=0.3[a2];[0:a][a2]amix=inputs=2" mischung.mp3
```
*`volume`* (Lautstärke) senkt hier die Musik auf 30 Prozent.
*`amix`* (Audios mischen) verbindet beide Tonspuren.

## 31. Video schneller abspielen
```bash
ffmpeg -i eingang.mp4 -filter:v "setpts=0.5*PTS" -filter:a "atempo=2.0" schnell.mp4
```
*`setpts`* (Zeitstempel) halbiert die Abspielzeit des Videos.
*`atempo`* (Geschwindigkeit des Tons) passt die Tonspur an.

## 32. Video rueckwaerts abspielen
```bash
ffmpeg -i eingang.mp4 -vf reverse -af areverse rueckwaerts.mp4
```
*`reverse`* (Ruecklauf) dreht das Bild um.
*`areverse`* spiegelt den Ton.

## 33. Video in Graustufen umwandeln
```bash
ffmpeg -i eingang.mp4 -vf "format=gray" grau.mp4
```
*`format=gray`* (Bildformat) entfernt die Farben.

## 34. Verwackeltes Video stabilisieren
```bash
ffmpeg -i wackelig.mp4 -vf deshake stabil.mp4
```
*`deshake`* (Bildstabilisierung) gleicht ruckelige Bewegungen aus.

## 35. Tonspur aus Video speichern
```bash
ffmpeg -i video.mp4 -vn -acodec copy ton.aac
```
*`-vn`* (Video nicht) entfernt das Bild.
*`-acodec copy`* speichert die Tonspur unveraendert.


## 36. Video komprimieren
```bash
ffmpeg -i input.mp4 -vcodec libx264 -crf 28 kleiner.mp4
```
*`libx264`* (Videocodec) komprimiert effizient.
*`crf`* (Qualitaetsfaktor) steuert die Dateigroesse.

## 37. Ton am Ende ausblenden
```bash
ffmpeg -i video.mp4 -af "afade=t=out:st=25:d=5" leise_end.mp4
```
*`afade`* (Ton ein- oder ausblenden) senkt die Lautstaerke langsam.
*`t=out`* bedeutet ausblenden. *`st`* (Startzeit) legt fest, wann es beginnt.
*`d`* (Dauer) bestimmt, wie lange der Effekt laeuft.

## 38. Video schaerfer machen
```bash
ffmpeg -i weich.mp4 -vf "unsharp" schaerfer.mp4
```
*`unsharp`* (Nachschaerfen) macht das Bild klarer.

## 39. Bild-in-Bild einsetzen
```bash
ffmpeg -i hintergrund.mp4 -i kleines.mp4 -filter_complex "overlay=W-w-10:H-h-10" pip.mp4
```
*`overlay`* (Ueberlagerung) legt das zweite Video oben rechts ab. *`W`* (Breite) und *`H`* (Hoehe) sind die Groesse des Hintergrunds. *`w`* und *`h`* beziehen sich auf das kleine Video.

## 40. Sepia-Faerbung anwenden
```bash
ffmpeg -i input.mp4 -vf "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131" sepia.mp4
```
*`colorchannelmixer`* (Farbmischer) erzeugt einen warmen Sepia-Ton.

## 41. Video spiegeln
```bash
ffmpeg -i eingang.mp4 -vf hflip gespiegelt.mp4
```
*`hflip`* (horizontal spiegeln) dreht das Bild so, als wuerde man es im
Spiegel sehen.

## 42. Bereich heranzoomen
```bash
ffmpeg -i eingang.mp4 -vf "crop=640:360:0:0,scale=1280:720" zoom.mp4
```
*`crop`* (Ausschnitt) waehlt einen kleineren Bereich aus. *`scale`*
(skalieren) vergroessert diesen Teil wieder auf die volle Groesse.

## 43. Video als GIF speichern
```bash
ffmpeg -i kurz.mp4 -vf "fps=12,scale=320:-1:flags=lanczos" kurz.gif
```
*`fps`* (Bilder pro Sekunde) bestimmt die Bildanzahl des GIF.
*`scale`* (skalieren) passt die Groesse an. *`-1`* behaelt das Seitenverhaeltnis.
*`lanczos`* ist ein Filter fuer eine schaerfere Darstellung.

## 44. Farben invertieren
```bash
ffmpeg -i normal.mp4 -vf negate negativ.mp4
```
*`negate`* (Farben umkehren) erzeugt ein Negativbild.

## 45. Text einblenden
```bash
ffmpeg -i video.mp4 -vf "drawtext=text='Hallo':fontcolor=white:fontsize=24:x=10:y=10" text.mp4
```
*`drawtext`* (Text einblenden) schreibt "Hallo" in das Bild. *`x`* und *`y`* bestimmen die Position.

## 46. Videos zusammenfuegen
Schreibe in eine Datei `liste.txt` je eine Zeile:
`file 'erstes.mp4'` und `file 'zweites.mp4'`.
```bash
ffmpeg -f concat -safe 0 -i liste.txt -c copy komplett.mp4
```
*`concat`* (aneinander haengen) fuegt die Clips zusammen. *`-c copy`* uebernimmt Bild und Ton unveraendert.

## 47. Video in Zeitlupe abspielen
```bash
ffmpeg -i clip.mp4 -filter:v "setpts=2.0*PTS" -filter:a "atempo=0.5" zeitlupe.mp4
```
*`setpts`* (Zeitstempel) verlaengert die Abspielzeit des Videos.
*`atempo`* (Tempo des Tons) halbiert die Geschwindigkeit der Tonspur.

## 48. Weiches Ein- und Ausblenden
```bash
ffmpeg -i clip.mp4 -vf "fade=t=in:st=0:d=2,fade=t=out:st=8:d=2" -af "afade=t=in:st=0:d=2,afade=t=out:st=8:d=2" weich.mp4
```
*`fade`* (Ein- oder Ausblenden) laesst das Bild langsam erscheinen oder verschwinden.
*`afade`* macht dasselbe fuer den Ton.

## 49. Videos nebeneinander zeigen
```bash
ffmpeg -i links.mp4 -i rechts.mp4 -filter_complex hstack nebeneinander.mp4
```
*`hstack`* (horizontal stapeln) platziert die Videos Seite an Seite.

## 50. Untertitel einbrennen
```bash
ffmpeg -i film.mp4 -vf subtitles=untertitel.srt mit_text.mp4
```
*`subtitles`* (Untertitel einblenden) fuegt die Texte dauerhaft ins Bild ein.


## 51. Tonrauschen reduzieren
```bash
ffmpeg -i laut.mp4 -af afftdn geraeusche_weniger.mp4
```
*`afftdn`* (Rauschfilter) entfernt stoerende Geraeusche aus der Tonspur.


## 52. Video stabilisieren
```bash
ffmpeg -i wacklig.mp4 -vf deshake ruhiger.mp4
```
*`deshake`* (Bildstabilisierung) gleicht Zittern aus.

