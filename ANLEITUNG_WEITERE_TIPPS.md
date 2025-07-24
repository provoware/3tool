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

