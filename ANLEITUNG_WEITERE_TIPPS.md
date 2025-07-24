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

