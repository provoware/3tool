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

## 53. Tonspur verschieben
```bash
ffmpeg -i video.mp4 -af "adelay=1000|1000" verschoben.mp4
```
*`adelay`* (Audio-Verzögerung) startet den Ton erst nach einer Sekunde.


## 54. Wasserzeichen hinzufuegen
```bash
ffmpeg -i video.mp4 -i logo.png -filter_complex "overlay=10:10" mit_logo.mp4
```
*`overlay`* (Ueberlagerung) legt das Logo an der Position 10:10 ins Bild.

## 55. Einzelbilder exportieren
```bash
ffmpeg -i video.mp4 bild_%03d.png
```
*`%03d`* zaehlt die Bilder mit drei Ziffern.

## 56. Video schneller abspielen
```bash
ffmpeg -i clip.mp4 -filter:v "setpts=0.5*PTS" -filter:a "atempo=2.0" schnell.mp4
```
*`setpts`* (Zeitstempel) verkuerzt die Videodauer.
*`atempo`* (Tempo des Tons) verdoppelt die Geschwindigkeit.

## 57. Ton normalisieren
```bash
ffmpeg -i leise.mp4 -af loudnorm normaler.mp4
```
*`loudnorm`* (Lautheitsnormalisierung) gleicht die Lautstaerke an.

## 58. Ton als WAV speichern
```bash
ffmpeg -i quelle.mp3 ziel.wav
```
*`wav`* ist ein unkomprimiertes Tonformat. Die Eingabe bleibt sonst unveraendert.

## 59. Vorschau-Bild erstellen
```bash
ffmpeg -i film.mp4 -ss 00:00:05 -vframes 1 vorschaubild.png
```
*`-ss`* setzt die Startzeit. *`-vframes 1`* speichert genau ein Bild.

## 60. Video drehen
```bash
ffmpeg -i eingang.mp4 -vf "transpose=1" gedreht.mp4
```
*`transpose`* (drehen) bewegt das Bild um 90 Grad im Uhrzeigersinn.

## 61. Farben kräftiger machen
```bash
ffmpeg -i eingang.mp4 -vf "eq=saturation=1.5" bunter.mp4
```
*`eq`* (Equalizer) passt Werte wie *`saturation`* (Farbintensität) an.

## 62. Farbton verändern
```bash
ffmpeg -i eingang.mp4 -vf "hue=h=60:s=0.8" farbig.mp4
```
*`hue`* (Farbton) verschiebt die Farben. *`h`* bestimmt die Richtung in Grad, *`s`* (Sättigung) senkt oder erhöht die Farbstärke.

## 63. Tonhöhe erhöhen
```bash
ffmpeg -i stimme.mp3 -filter:a "asetrate=44100*1.2,atempo=1/1.2" hoeher.mp3
```
*`asetrate`* (Abtastrate) beschleunigt die Tonhöhe. *`atempo`* (Geschwindigkeit) gleicht die Abspielgeschwindigkeit wieder an.

## 64. Bereich mit farbigem Rahmen hervorheben
```bash
ffmpeg -i eingang.mp4 -vf "drawbox=x=100:y=50:w=200:h=100:color=red@0.5:thickness=5" markiert.mp4
```
*`drawbox`* (Rechteck zeichnen) legt einen Rahmen aufs Bild. *`x`* und *`y`* sind die Position, *`w`* (Breite) und *`h`* (Höhe) bestimmen die Größe, *`color`* gibt die Farbe an und *`thickness`* die Strichstärke.

## 65. Echoeffekt bei Ton anwenden
```bash
ffmpeg -i sprache.mp3 -af "aecho=0.8:0.88:60:0.4" echo.mp3
```
*`aecho`* (Echo) fügt einen Nachhall hinzu. Die Zahlen stehen für Eingangslautstärke, Echo-Lautstärke, Verzögerung in Millisekunden und Abklingen.

## 66. Gruenen Hintergrund ersetzen
```bash
ffmpeg -i greenscreen.mp4 -i hintergrund.jpg -filter_complex "[0:v]colorkey=0x00FF00:0.3:0.1[fg];[1:v][fg]overlay" neuer_hintergrund.mp4
```
*`colorkey`* (Farbe entfernen) macht Gruen durchsichtig. *`overlay`* (Ueberlagern) legt das Video auf das neue Bild.

## 67. Video im Raster anzeigen
```bash
ffmpeg -i clip.mp4 -filter:v "tile=2x2" raster.mp4
```
*`tile`* (Kachelmodus) ordnet Kopien des Videos in 2 Spalten und 2 Reihen an.

## 68. Video mehrmals hintereinander abspielen
```bash
ffmpeg -stream_loop 2 -i clip.mp4 -c copy schleife.mp4
```
*`-stream_loop`* (Wiederholen) laesst das Video hier insgesamt dreimal laufen, ohne es neu zu kodieren.

## 69. Zwei Clips weich ueberblenden
```bash
ffmpeg -i anfang.mp4 -i ende.mp4 -filter_complex "xfade=transition=fade:duration=1:offset=5" uebergang.mp4
```
*`xfade`* (Ueberblenden) erzeugt einen weichen Uebergang. *`transition`* legt die Art fest, *`duration`* dauert eine Sekunde und *`offset`* gibt an, wann die Ueberblendung beginnt.

## 70. Video vertikal spiegeln
```bash
ffmpeg -i eingang.mp4 -vf vflip kopfueber.mp4
```
*`vflip`* (vertikal spiegeln) dreht das Bild auf den Kopf.

## 71. Schwarze Balken abschneiden
```bash
ffmpeg -i film.mp4 -vf "crop=iw:ih-80:0:40" ohne_balken.mp4
```
*`crop`* (Bild zuschneiden) behaelt die volle Breite *`iw`*. *`ih-80`* nimmt 80 Pixel von der Hoehe weg, *`0:40`* verschiebt den Ausschnitt um 40 Pixel nach unten.

## 72. Video weichzeichnen
```bash
ffmpeg -i eingang.mp4 -vf "gblur=sigma=5" weich.mp4
```
*`gblur`* (Gauss-Weichzeichner) macht das Bild unscharf. *`sigma`* (Staerke) legt fest, wie stark der Effekt ist.

## 73. Schwarze Raender hinzufuegen
```bash
ffmpeg -i eingang.mp4 -vf "pad=iw+100:ih+100:50:50:color=black" mit_rand.mp4
```
*`pad`* (auffuellen) vergroessert die Flaeche. *`iw+100`* und *`ih+100`* fuegen je 100 Pixel hinzu, *`50:50`* positioniert das Original mittig.

## 74. Tonhöhe verringern
```bash
ffmpeg -i stimme.mp3 -filter:a "asetrate=44100*0.8,atempo=1/0.8" tiefer.mp3
```
*`asetrate`* (Abtastrate) senkt die Tonhöhe. *`atempo`* (Geschwindigkeit) passt die Abspielgeschwindigkeit wieder an.

## 75. Bildrauschen reduzieren
```bash
ffmpeg -i video.mp4 -vf "hqdn3d" sauber.mp4
```
*`hqdn3d`* (High Quality 3D Denoise) glättet das Bild und mindert Rauschen.

## 76. Zeilensprungartefakte entfernen
```bash
ffmpeg -i eingang.mp4 -vf yadif sauber.mp4
```
*`yadif`* (Yet Another Deinterlacing Filter) beseitigt das Zeilenflimmern bei alten Aufnahmen.

## 77. Gamma korrigieren
```bash
ffmpeg -i video.mp4 -vf "eq=gamma=1.3" klarer.mp4
```
*`gamma`* (Helligkeitsverteilung) hellt mittlere Bildbereiche auf. Der Wert `1.3` sorgt für mehr Leuchtkraft.

## 78. Bitrate begrenzen
```bash
ffmpeg -i video.mp4 -b:v 1000k -b:a 128k kleiner.mp4
```
*`b:v`* (Video-Bitrate) legt die Datenrate des Bildes fest. Mit `1000k` wird es kleiner.
*`b:a`* (Audio-Bitrate) stellt die Datenrate des Tons ein.

## 79. Video halb so groß speichern
```bash
ffmpeg -i eingang.mp4 -vf "scale=iw/2:ih/2" halb.mp4
```
`scale` (skalieren) teilt Breite und Höhe durch zwei.

## 80. Seitenverhältnis anpassen
```bash
ffmpeg -i clip.mp4 -vf "setdar=16/9" breitbild.mp4
```
`setdar` (Display Aspect Ratio) gibt das Verhältnis von Breite zu Höhe an. Mit 16/9 erscheint das Bild richtig.

## 81. Video in WebM speichern
```bash
ffmpeg -i eingang.mp4 -c:v libvpx-vp9 -c:a libopus ausgabe.webm
```
*`libvpx-vp9`* (Videocodec) komprimiert modern, *`libopus`* (Audiocodec) liefert guten Klang.

## 82. Lauftext einblenden
```bash
ffmpeg -i video.mp4 -vf "drawtext=text=Hallo\\ :fontcolor=white:fontsize=24:x=w/2-text_w/2:y=h-40*t" abspann.mp4
```
*`drawtext`* (Text einblenden) zeigt "Hallo" und lässt den Text nach oben wandern, weil `t` die Zeit ist.


## 83. Nur einen Ausschnitt speichern
```bash
ffmpeg -ss 00:01:00 -i eingang.mp4 -t 30 -c copy ausschnitt.mp4
```
*`-ss`* (Startzeit) springt zu Minute 1. *`-t`* (Dauer) nimmt danach 30 Sekunden. *`-c copy`* kopiert Bild und Ton ohne Neukodierung.

## 84. Video in Graustufen umwandeln
```bash
ffmpeg -i eingang.mp4 -vf format=gray graustufen.mp4
```
*`format=gray`* (Farbraum) verwandelt das Bild in Schwarzweiß.

## 85. Video in MKV umwandeln
```bash
ffmpeg -i eingang.mp4 -c copy ausgabe.mkv
```
*`-c copy`* (Stream-Kopie) überträgt Bild und Ton unverändert in die neue **MKV**-Datei (Matroska-Container).

## 86. Datum ins Bild schreiben
```bash
ffmpeg -i eingang.mp4 -vf "drawtext=text='%{localtime}':fontcolor=white:x=10:y=10" datumsanzeige.mp4
```
*`drawtext`* (Textfilter) zeigt das aktuelle Datum an. *`%{localtime}`* steht für die Tageszeit.

