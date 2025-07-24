# Weitere einfache Tipps

Diese kurze Sammlung richtet sich an absolute Einsteiger. Jeder Befehl ist komplett notiert. Fachbegriffe stehen in Klammern und werden erklärt.

## 1. Slideshow schneller oder langsamer

Die Dauer pro Bild lässt sich steuern. Beispiel: Jede Datei zwei Sekunden anzeigen:

```bash
ffmpeg -y -framerate 0.5 -pattern_type glob -i "bilder/*.jpg" -i musik.mp3 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" \
  -c:v libx264 -c:a aac -b:a 192k -shortest slideshow.mp4
```

`-framerate 0.5` bedeutet hier 0,5 Bilder pro Sekunde (also zwei Sekunden pro Bild).

## 2. Video auf Audiolänge bringen

Wenn der Film kürzer ist als die Tonspur, lässt sich das Ende einfrieren. Das erledigt der **tpad-Filter** (letztes Bild wird mehrfach verwendet):

```bash
ffmpeg -i video.mp4 -i kommentar.mp3 -vf "tpad=stop_mode=clone:stop_duration=10" \
  -c:v libx264 -c:a aac -b:a 192k -shortest neues_video.mp4
```

`stop_duration=10` verlängert das Video um zehn Sekunden.

## 3. Ein Bild für viele Audiodateien

Mehrere Audios lassen sich mit nur einem Bild verarbeiten. Jedes Audio ergibt ein eigenes Video:

```bash
python3 videobatch_extra.py --mode multi-audio --img titelbild.jpg --aud *.mp3 --out output
```

Das Sternchen (`*`) steht für "alle Dateien" in diesem Ordner.

