# Zusätzliche Modi

Diese Anleitung beschreibt drei neue Möglichkeiten, Videos zu erstellen. Die Sprache ist bewusst einfach gehalten. Fachbegriffe stehen in Klammern und werden kurz erklärt.

## 1. Slideshow (Bilderserie)

Mehrere Bilder werden nacheinander gezeigt und eine Audiodatei läuft im Hintergrund.

1. Lege alle Bilder in einen Ordner, zum Beispiel `bilder/`.
2. Starte dann den folgenden Befehl:
   ```bash
   python3 videobatch_extra.py --mode slideshow --img bilder --aud musik.mp3 --out output
   ```
   Jedes Bild wird gleich lang gezeigt. Die Gesamtlänge richtet sich nach der Audiodatei.

## 2. Video mit neuer Tonspur

Ein vorhandenes Video bekommt eine eigene Audiodatei. Die Länge des Videos wird automatisch angepasst.

```bash
python3 videobatch_extra.py --mode video --img film.mp4 --aud kommentar.mp3 --out output
```

`--mode video` ersetzt die bisherige Tonspur (Audio) des Videos.

## 3. Ein Bild für viele Audios

Mehrere Audiodateien sollen alle dasselbe Bild verwenden.

```bash
python3 videobatch_extra.py --mode multi-audio --img bild.jpg --aud a1.mp3 a2.mp3 a3.mp3 --out output
```

Für jede Audiodatei wird ein eigenes Video erstellt. Das Bild bleibt stets gleich.
