# Zusätzliche Hinweise

Dieses Dokument sammelt weitere Vorschläge für Neulinge. Die Erklärungen sind bewusst einfach. Fachbegriffe stehen in Klammern und werden kurz erläutert.

## 1. Videos verkleinern

Wenn die Ausgabedateien zu groß sind, kann man die Auflösung (Bildgröße) verringern. Beispiel:

```bash
python3 videobatch_extra.py --img bild.jpg --aud ton.mp3 --width 1280 --height 720
```

`width` und `height` bestimmen die Breite und Höhe in Pixeln.

## 2. Audio-Bitrate anpassen

Die Option `--abitrate` legt fest, wie viele Daten pro Sekunde für den Ton genutzt werden. Niedrigere Werte sparen Platz, klingen aber schlechter.

```bash
python3 videobatch_extra.py --img bild.jpg --aud ton.mp3 --abitrate 128k
```

`abitrate` steht für "Audio Bitrate" (Tonqualität pro Sekunde).

## 3. Videos zuschneiden

Mit dem Filter `crop` aus `ffmpeg` kann man Bildränder entfernen.

```bash
ffmpeg -i eingang.mp4 -filter:v "crop=640:360:0:0" ausgegeben.mp4
```

Hier bleibt nur der Bereich 640x360 Pixel ab der oberen linken Ecke übrig.

## 4. Ton lauter machen

Falls eine Aufnahme zu leise ist, hilft der `volume`-Filter.

```bash
ffmpeg -i leise.mp3 -filter:a "volume=1.8" laut.mp3
```

Die Zahl 1.8 bedeutet 180% der ursprünglichen Lautstärke.

Weitere Hilfen gibt es in den anderen Anleitungen.
