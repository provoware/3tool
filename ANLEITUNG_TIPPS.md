# Weitere Tipps

Diese Hinweise richten sich an Einsteiger, die noch mehr aus dem Tool herausholen möchten. Die Sprache ist bewusst einfach gehalten. Fachbegriffe stehen in Klammern und werden kurz erklärt.

## Projektdateien verwalten

1. **Projekt speichern** – über den Knopf "Projekt speichern" wird eine Datei `projekt.json` erstellt. Darin stehen alle Paare und Einstellungen.
2. **Projekt laden** – mit "Projekt laden" kann diese Datei wieder geöffnet werden.

## ffmpeg prüfen

`ffmpeg` (das eigentliche Programm zum Kodieren) sollte installiert sein. Testen:

```bash
ffmpeg -version
```

Fehlt es, kann es unter Debian/Ubuntu so installiert werden:

```bash
sudo apt-get install ffmpeg
```

## Ordner im Dateimanager öffnen

Im Tabellenbereich kann man nun mit der rechten Maustaste auf eine Zeile klicken und "Im Ordner zeigen" auswählen. Dadurch öffnet sich der Ordner, in dem sich die Datei befindet.

## Schriftgröße reparieren

Wenn die Schrift unerwartet sehr groß oder klein erscheint, ist vielleicht eine falsche Einstellung gespeichert. Wähle im Menü **Ansicht** den Punkt **Schrift Reset**, um zur Standardgröße 11 zurückzukehren. Bleibt das Problem bestehen, lösche die Datei `~/.config/Provoware/VideoBatchTool.conf` (Konfigurationsdatei) und starte das Programm neu.

## Fehlermeldungen finden

Bei einem unerwarteten Fehler zeigt das Programm ein rotes Hinweisfenster. Die ausführliche Meldung steht im Logfile (Protokolldatei) unter `~/.videobatchtool/logs`. Öffne die neueste Datei dort mit einem Texteditor, um die Details zu sehen.

## Weitere Befehle

Das Tool lässt sich auch komplett über die Kommandozeile nutzen:

```bash
python3 videobatch_extra.py --img bild.jpg --aud ton.mp3 --out output
```

Dieser Befehl erstellt ein einzelnes Video ohne die GUI.

## Slideshow mit vielen Bildern
```bash
python3 videobatch_extra.py --mode slideshow --img bilder/ --aud musik.mp3 --out output
```
Dabei wird ein ganzer Ordner voller Bilder nacheinander gezeigt.

## Vorhandenes Video mit neuem Ton
```bash
python3 videobatch_extra.py --mode video --img film.mp4 --aud kommentar.mp3 --out output
```
`--mode video` nutzt das vorhandene Bildmaterial und ersetzt nur die Tonspur.

## Gleiches Bild für mehrere Audios
```bash
python3 videobatch_extra.py --mode multi-audio --img bild.jpg --aud sprache*.mp3 --out output
```
`multi-audio` erstellt für jede Audiodatei ein eigenes Video mit demselben Bild.

## Video spiegeln
```bash
ffmpeg -i eingang.mp4 -vf "hflip" gespiegelt.mp4
```
`hflip` (horizontal spiegeln) dreht das Bild an einer senkrechten Achse.

## Kontrast erhöhen
```bash
ffmpeg -i eingang.mp4 -vf "eq=contrast=1.5" kontrast.mp4
```
`eq` (Equalizer) verändert Helligkeit und Kontrast. Der Wert `1.5` sorgt für ein intensiveres Bild.

## Nur die ersten 30 Sekunden
```bash
ffmpeg -i eingang.mp4 -ss 0 -t 30 -c copy kurz.mp4
```
`-ss` legt den Startpunkt fest, `-t` die Dauer. Hier wird nur der erste Abschnitt übernommen.
