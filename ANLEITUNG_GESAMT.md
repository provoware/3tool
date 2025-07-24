# Gesamtanleitung VideoBatchTool

Diese Anleitung fasst alle bisherigen Hilfen zusammen. Die Sprache ist bewusst einfach. Fachbegriffe stehen in Klammern und werden kurz erklaert.

## 1. Installation und Start

1. Terminal (Eingabe-Fenster) oeffnen und in den Projektordner wechseln. Beispiel:
   ```bash
   cd ~/Downloads/VideoBatchTool
   ```
2. Virtuelle Umgebung ("virtual environment" – isolierter Python-Bereich) anlegen:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Abhaengigkeiten (benoetigte Pakete) installieren:
   ```bash
   pip install -r requirements.txt
   ```
4. Programm starten:
   ```bash
   python3 videobatch_launcher.py
   ```
   Der Launcher prueft alles und startet die grafische Oberflaeche (GUI).
5. Selbsttest ohne GUI:
   ```bash
   python3 videobatch_extra.py --selftest
   ```
   Bei Erfolg erscheint "Selftests OK".

## 2. Grundsaetzliche Nutzung

Ein einzelnes Bild mit einer Audiodatei verarbeiten:
```bash
python3 videobatch_extra.py --img bild.jpg --aud musik.mp3 --out output
```
Das Ergebnis landet im Ordner `output`.

## 3. Slideshow (mehrere Bilder)

Alle Bilder eines Ordners nacheinander zeigen und eine Tonspur abspielen. Jedes Bild wird automatisch passend lang eingeblendet:
```bash
python3 videobatch_extra.py --mode slideshow --img bilder --aud kommentar.mp3 --out output
```
`--mode slideshow` nutzt den gesamten Ordner `bilder/`.

## 4. Video laenger machen (Video + Audio)

Ein vorhandenes Video mit neuer Tonspur kombinieren. Ist das Audio laenger, wird das letzte Bild eingefroren ("tpad"-Filter):
```bash
python3 videobatch_extra.py --mode video --img film.mp4 --aud kommentar.mp3 --out output
```

## 5. Ein Bild fuer viele Audios

Mehrere Audiodateien sollen das gleiche Bild verwenden. Fuer jede Tonspur entsteht ein Video:
```bash
python3 videobatch_extra.py --mode multi-audio --img titelbild.jpg --aud a1.mp3 a2.mp3 a3.mp3 --out output
```
Das Sternchen (`*`) in der Shell steht fuer "alle Dateien" in einem Ordner.

## 6. Weitere Befehle mit ffmpeg

Videos aneinanderhaengen ("concat" = zusammenfuehren):
```bash
ffmpeg -f concat -safe 0 -i liste.txt -c copy komplett.mp4
```

Nur die Tonspur sichern:
```bash
ffmpeg -i video.mp4 -vn -acodec copy ton.mp3
```

Film schneller abspielen:
```bash
ffmpeg -i input.mp4 -filter:v "setpts=0.5*PTS" schnell.mp4
```

Wasserzeichen einfuegen:
```bash
ffmpeg -i video.mp4 -i logo.png -filter_complex "overlay=10:10" mit_logo.mp4
```

## 7. Weitere Tipps

*Viele Videos automatisch verarbeiten* ("loop" – wiederholt den Befehl):
```bash
for img in samples/*.jpg; do
    aud="${img%.jpg}.mp3"
    python3 videobatch_extra.py --img "$img" --aud "$aud" --out output
done
```

*Ausgabeordner* aendern:
```bash
python3 videobatch_extra.py --img bild.jpg --aud ton.mp3 --out /pfad/zum/ziel
```

*Qualitaet* steuern:
```bash
python3 videobatch_extra.py --img bild.jpg --aud ton.mp3 --crf 18
```
`crf` bedeutet "Constant Rate Factor" (Qualitaetsfaktor).

*Videos verkleinern*:
```bash
python3 videobatch_extra.py --img bild.jpg --aud ton.mp3 --width 1280 --height 720
```
`width` und `height` geben die Groesse in Pixeln an.

*Audio-Bitrate* anpassen:
```bash
python3 videobatch_extra.py --img bild.jpg --aud ton.mp3 --abitrate 128k
```
`abitrate` steht fuer "Audio Bitrate" (Tonqualitaet pro Sekunde).

*Videos zuschneiden*:
```bash
ffmpeg -i eingang.mp4 -filter:v "crop=640:360:0:0" ausgegeben.mp4
```
`crop` entfernt Randbereiche.

*Ton lauter machen*:
```bash
ffmpeg -i leise.mp3 -filter:a "volume=1.8" laut.mp3
```
`volume` gibt den Faktor fuer die Lautstaerke an (1.8 = 180%).

*Logdatei ansehen*:
Ueber das Hilfe-Menue laesst sich "Logdatei oeffnen" auswaehlen. Dort stehen weitere Details, falls etwas schiefgeht.

