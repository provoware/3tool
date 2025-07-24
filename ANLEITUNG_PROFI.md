# Profi-Tipps fuer VideoBatchTool

Diese Anleitung richtet sich an fortgeschrittene Laien. Sie erklaert komplexere Kommandos in einfacher Sprache. Fachbegriffe stehen wie gewohnt in Klammern und werden kurz erlaeutert.

## 1. Mehrere Videos hintereinander (Batch-Verarbeitung)
```bash
for vid in clips/*.mp4; do
    aud="${vid%.mp4}.mp3"
    python3 videobatch_extra.py --mode video --img "$vid" --aud "$aud" --out fertige_videos
done
```
*`for`* startet eine Schleife. Fuer jede Datei im Ordner `clips` wird eine passende Audiodatei gesucht und verarbeitet.

## 2. Video beschleunigen (Playback-Speed)
```bash
ffmpeg -i input.mp4 -filter:v "setpts=0.75*PTS" schneller.mp4
```
*`setpts`* steuert die Wiedergabegeschwindigkeit. Ein Faktor von `0.75` macht das Video 25 % schneller.

## 3. Untertitel hinzufuegen (Subtitles)
```bash
ffmpeg -i film.mp4 -i text.srt -c copy -c:s mov_text film_mit_untertiteln.mp4
```
*`mov_text`* ist ein Untertitel-Codec, der von vielen Playern verstanden wird.

## 4. Eigenes Preset verwenden (Voreinstellung)
```bash
python3 videobatch_extra.py --img bild.jpg --aud ton.mp3 --preset slower --crf 18
```
*`preset`* bestimmt die Rechengeschwindigkeit. *`slower`* braucht laenger, liefert aber bessere Qualitaet.

## 5. Fehlermeldungen analysieren
Wenn die GUI nicht startet und `libGL.so.1` vermisst wird, hilft unter Debian/Ubuntu der Befehl:
```bash
sudo apt install libgl1
```
Danach das Programm erneut starten.

Weitere Hinweise findest du in `ANLEITUNG_GESAMT.md` und den anderen Dokumenten.
