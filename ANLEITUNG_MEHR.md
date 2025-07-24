# Noch mehr Tipps

Dieses Dokument bietet weitere Anregungen für Neulinge, die das Tool besser nutzen wollen. Fachbegriffe stehen in Klammern und werden kurz erläutert.

## Videos stapelweise erstellen

Hat man viele Bild/Audio-Paare in einem Ordner, kann man sie automatisch abarbeiten. Dazu nutzt man eine sogenannte *Schleife* (loop). Im Terminal wäre das:

```bash
for aud in audio/*.mp3; do
    img="${aud%.mp3}.jpg"
    python3 videobatch_extra.py --img "$img" --aud "$aud" --out output
done
```

Dabei wird pro Runde `videobatch_extra.py` (die Kommandozeilenversion) aufgerufen.

## Lautstärke anpassen

Mit `--abitrate` legt man die Audio-Qualität fest. Wer die Lautstärke ändern möchte, kann `ffmpeg` direkt benutzen:

```bash
ffmpeg -i ton.mp3 -filter:a "volume=1.5" lauter.mp3
```

Der Filter `volume` erhöht hier die Lautstärke um das 1,5-Fache.

## Pfade schneller öffnen

Im Hauptfenster gibt es nun einen Knopf neben dem Feld "Ausgabeordner". Ein Klick öffnet den Ordner im Dateimanager.

## Logdatei einsehen

Alle Vorgänge schreibt das Programm in eine *Logdatei* (Protokoll). Die Datei lässt sich über das Menü "Hilfe" öffnen.
