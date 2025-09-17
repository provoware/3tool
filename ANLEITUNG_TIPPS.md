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

Noch mehr Kontrolle über die Präsentation:

* `--image-duration 5` hält jedes Bild exakt 5 Sekunden lang ("Image Duration" = Bilddauer).
* `--audio-fade 2` sorgt für sanfte Übergänge am Anfang und Ende des Tons ("Fade" = Überblendung).
* `--background "#101010"` setzt die Randfarbe (Hex-Farbe = Farbcode mit #RRGGBB).
* `--video-filter "zoompan=z='min(zoom+0.001,1.3)':d=150"` erzeugt eine leichte Bewegung ("zoompan" = Zoom/Schwenk-Effekt).
* `--order mtime` sortiert nach Änderungszeit ("mtime" = "modified time"). Alternativen: `natural` (Standard, versteht Zahlen), `name` (alphabetisch).
* `--reverse` kehrt die Reihenfolge um ("Reverse" = rückwärts).
* `--shuffle` mischt alle Bilder ("Shuffle" = zufällig).
* `--shuffle-seed 2024` liefert die gleiche Zufallsreihenfolge bei jedem Lauf ("Seed" = Startwert).
* `--image-fit cover` füllt den Bildschirm vollständig aus ("Cover" = zuschneiden). Für vollständige Sichtbarkeit wähle `contain`.
* `--image-extensions "*.jpg,*.png"` grenzt die Dateitypen ein ("Extensions" = Endungen).
* `--video-codec libx265` nutzt moderne Videokompression ("Codec" = Kodierverfahren). Standard ist `libx264`.
* `--audio-codec copy` übernimmt den Ton unverändert. Ideal, wenn das Audio bereits passt.
* `--pix-fmt yuv420p` stellt ein kompatibles Farbprofil sicher ("Pixel Format" = Farbauflösung). `--pix-fmt none` lässt FFmpeg entscheiden.
* `--movflags +faststart` sorgt für schnelles Starten im Webplayer ("movflags" = Container-Flag). Mit `--movflags none` lässt sich das deaktivieren.
* `--video-bitrate 5M` erzwingt eine feste Datenrate. Bei gleichzeitiger `--crf`-Angabe weist das Tool auf mögliche FFmpeg-Warnungen hin.
* `--video-tune animation` optimiert die Kodierung für Trickfilme ("Tune" = Feineinstellung). `--video-tune none` schaltet es aus.
* `--video-profile main` bestimmt die Profilstufe ("Profile" = Qualitätsstufe im Codec) für Geräte mit festen Anforderungen.
* `--video-level 4.1` stellt das Level ("Level" = Leistungsstufe) ein, z. B. für Blu-ray- oder Streaming-Vorgaben.
* `--gop-size 60` steuert den Abstand zwischen Schlüsselbildern ("GOP" = Gruppe von Bildern).
* `--video-maxrate 8M` begrenzt die Spitzenbitrate ("Maxrate" = maximale Datenrate) und `--video-bufsize 16M` legt den Puffer fest.
* `--audio-bitrate 160k` ist ein zweiter Name für `--abitrate` und legt die Tonqualität fest.
* `--audio-sample-rate 48000` stellt die Abtastrate ein ("Sample Rate" = Messpunkte pro Sekunde).
* `--audio-channels 2` definiert die Kanalzahl ("Channels" = Tonspuren, z. B. Stereo).
* `--audio-normalize` aktiviert automatische Lautheitsanpassung ("Loudness" = wahrgenommene Lautstärke) über den `loudnorm`-Filter.

Tipp: Mehrere Optionen lassen sich einfach kombinieren. Beispiel:
```bash
python3 videobatch_extra.py --mode slideshow --img bilder/ --aud musik.mp3 --out output \
  --image-duration 5 --background "#101010" --audio-fade 2 \
  --order natural --image-fit contain --video-filter "eq=saturation=1.2" \
  --video-codec libx264 --pix-fmt yuv420p --audio-normalize
```

Mit zufälliger Mischung und Beschnitt für Vollbild:
```bash
python3 videobatch_extra.py --mode slideshow --img bilder/ --aud musik.mp3 --out output \
  --shuffle --shuffle-seed 99 --image-fit cover --background "#111111" \
  --audio-fade 2.5 --movflags +faststart --video-tune film --video-profile high
```

Stabiles Streaming mit fixem Datenbudget:
```bash
python3 videobatch_extra.py --mode slideshow --img event/ --aud keynote.mp3 --out stream \
  --video-bitrate 4M --video-maxrate 5M --video-bufsize 10M --gop-size 48 \
  --audio-bitrate 160k --audio-sample-rate 48000 --audio-channels 2
```

Neu: Vor jedem Rendern erscheint im Terminal ein kurzer "Slideshow-Check". Er nennt Anzahl der Bilder, verwendete Filter, Profile, Normalisierung, Fade-Zeiten, Datenraten sowie ggf. entfernte Duplikate und den Ausgabepfad. Tritt ein Fehler auf (zum Beispiel fehlende Dateien, negative Werte oder leere Codec-Namen), stoppt der Befehl sofort mit einer gut lesbaren Erklärung.

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
