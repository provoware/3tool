# Praktische Beispiele

Diese kurze Anleitung gibt weitere Tipps in einfacher Sprache. Fachbegriffe stehen in Klammern und werden erklärt.

## 1. Slideshow anpassen

Um die Anzeigedauer pro Bild zu ändern, kann man den FFmpeg-Befehl direkt aufrufen:

```bash
ffmpeg -y -framerate 1 -pattern_type glob -i "bilder/*.jpg" -i musik.mp3 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" \
  -c:v libx264 -c:a aac -b:a 192k -shortest slideshow.mp4
```

`-framerate 1` bestimmt hier die Dauer (1 Bild pro Sekunde). Die Option `glob` erlaubt Platzhalter wie `*.jpg`.

## 2. Video auf Audiolänge strecken

Ist das Video kürzer als die Audiodatei, lässt sich das letzte Bild einfrieren ("tpad"-Filter):

```bash
ffmpeg -i video.mp4 -i kommentar.mp3 -vf "tpad=stop_mode=clone:stop_duration=5" \
  -c:v libx264 -c:a aac -b:a 192k -shortest kombi.mp4
```

`stop_duration=5` verlängert das Video um 5 Sekunden.

## 3. Ein Bild für viele Audios

Mehrere Tonspuren lassen sich bequem verarbeiten:

```bash
python3 videobatch_extra.py --mode multi-audio --img bild.jpg --aud a1.mp3 a2.mp3 a3.mp3 --out output
```

Pro Audiodatei entsteht ein eigenes Video.
