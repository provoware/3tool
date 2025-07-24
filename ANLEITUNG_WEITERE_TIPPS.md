# Weitere einfache Befehle

Diese kurze Liste zeigt nützliche ffmpeg-Kommandos in leichter Sprache. Fachbegriffe stehen in Klammern und werden erklärt.

## Zwei Videos aneinanderhängen
```bash
ffmpeg -i teil1.mp4 -i teil2.mp4 -filter_complex "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1" zusammen.mp4
```
Damit werden zwei Eingänge ("Inputs") direkt hintereinander verbunden.

## Tonspur aus Video speichern
```bash
ffmpeg -i film.mp4 -vn -acodec copy tonspur.aac
```
`-vn` bedeutet "kein Video" und speichert nur die Audio-Daten ("codec" = Kodierungsverfahren).

## Kurzes Beispiel zum Zuschneiden (cropping)
```bash
ffmpeg -i quelle.mp4 -filter:v "crop=1280:720:0:0" ausschnitt.mp4
```
Hier wird nur ein 1280×720 Bereich ab der linken oberen Ecke behalten.

## Video drehen
```bash
ffmpeg -i eingang.mp4 -vf "transpose=1" gedreht.mp4
```
`transpose` (drehen) richtet das Video neu aus. Der Wert `1` steht für eine
90° Drehung gegen den Uhrzeigersinn.

## Geschwindigkeit verdoppeln
```bash
ffmpeg -i clip.mp4 -filter:v "setpts=0.5*PTS" doppelt.mp4
```
Der `setpts`-Filter verkürzt hier die Bilddauer. Dadurch läuft das Video doppelt
so schnell.

## Video spiegeln
```bash
ffmpeg -i quelle.mp4 -vf "hflip" gespiegelt.mp4
```
Der Filter `hflip` spiegelt das Bild horizontal wie in einem Spiegel.

## Kurzen Ausschnitt speichern
```bash
ffmpeg -ss 00:00:05 -i lang.mp4 -t 00:00:10 -c copy teil.mp4
```
`-ss` gibt den Startzeitpunkt an, `-t` die Dauer. Hier wird ein zehn Sekunden langer Abschnitt ab Sekunde 5 ausgegeben.

## Video in Schwarz-Weiß umwandeln
```bash
ffmpeg -i bunt.mp4 -vf format=gray grau.mp4
```
`format=gray` (Graustufen) macht das Video komplett schwarz-weiß.

## Größe ändern
```bash
ffmpeg -i eingang.mp4 -vf scale=1280:720 kleiner.mp4
```
`scale` (Skalierung) passt Breite und Höhe des Bildes an.


## Video langsamer abspielen
```bash
ffmpeg -i clip.mp4 -filter:v "setpts=2*PTS" langsam.mp4
```
`setpts` (Zeitstempel) verdoppelt die Wiedergabedauer und macht das Video halb so schnell.

## Ton normalisieren
```bash
ffmpeg -i laut.mp3 -af loudnorm normal.mp3
```
`loudnorm` (Lautheitsausgleich) sorgt fuer ein einheitliches Lautstaerkeniveau.

## Untertitel einbinden
```bash
ffmpeg -i video.mp4 -i text.srt -c:v copy -c:a copy -c:s mov_text mit_untertitel.mp4
```
`mov_text` ist das Untertitelformat fuer MP4-Dateien.

## Video ohne Ton speichern
```bash
ffmpeg -i film.mp4 -an stumm.mp4
```
`-an` (audio none) entfernt die Tonspur.

## Einzelnes Bild aus Video speichern
```bash
ffmpeg -ss 00:00:10 -i film.mp4 -vframes 1 bild.png
```
`-vframes 1` (ein Bild) nimmt genau einen Frame ab der gewählten Zeit.

## Video rückwärts abspielen
```bash
ffmpeg -i film.mp4 -vf reverse -af areverse rueckwaerts.mp4
```
Die Filter `reverse` und `areverse` (umkehren) lassen Bild und Ton rückwärts laufen.

## Tonspur zeitlich verschieben
```bash
ffmpeg -i film.mp4 -af adelay=2000|2000 verschoben.mp4
```
`adelay` (Audio-Verzögerung) schiebt die Tonspur hier um zwei Sekunden nach hinten. Die zwei Werte stehen für linke und rechte Spur.

## Metadaten eines Videos anzeigen
```bash
ffprobe -v quiet -show_format -show_streams eingang.mp4
```
`ffprobe` ist ein Analyse-Programm von ffmpeg. Es listet alle Daten wie Auflösung und Kodierung auf.

## Untertitel aus Video speichern
```bash
ffmpeg -i film.mp4 -map 0:s:0 subs.srt
```
`-map` (Zuordnung) wählt hier die erste Untertitelspur und speichert sie als
`subs.srt`.

## Verwackeltes Video stabilisieren
```bash
ffmpeg -i wackelig.mp4 -vf deshake stabil.mp4
```
`deshake` versucht, sichtbare Bewegungen zu glätten.

## Dateigröße verringern
```bash
ffmpeg -i grosses_video.mp4 -vcodec libx264 -crf 28 kleiner.mp4
```
`libx264` ist ein verbreiteter Videocodec (Kompressionsverfahren). Ein höherer
`crf`-Wert (Qualitätsfaktor) führt zu kleinerer Datei, allerdings mit etwas
weniger Bildqualität.

## Schwarze Ränder abschneiden
```bash
ffmpeg -i film.mp4 -vf "crop=1280:720:0:60" ohne_rand.mp4
```
Der Filter `crop` (beschneiden) entfernt hier oben und unten 60 Pixel und gibt
ein 1280 × 720-Bild zurück.

## Text ins Bild schreiben
```bash
ffmpeg -i eingang.mp4 -vf "drawtext=text='Hallo':fontcolor=white:x=10:y=10" mit_text.mp4
```
`drawtext` (Text einblenden) fügt Schrift an der angegebenen Position ein.

## Video als GIF speichern
```bash
ffmpeg -i kurz.mp4 -vf "fps=10,scale=320:-1:flags=lanczos" anim.gif
```
Damit entsteht aus dem Video eine animierte GIF-Datei.

## Jede Sekunde ein Bild speichern
```bash
ffmpeg -i film.mp4 -vf fps=1 bilder/bild_%03d.png
```
`fps=1` (Frames pro Sekunde) legt hier fest, dass genau ein Bild pro Sekunde ausgegeben wird.

