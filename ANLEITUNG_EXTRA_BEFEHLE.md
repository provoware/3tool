# Weitere Befehlsbeispiele

Diese Sammlung richtet sich an Laien und erklaert jeden Schritt. Fachbegriffe stehen in Klammern und werden kurz beschrieben.

## 1. Videos zusammenfuegen

Wenn mehrere Clips nacheinander abgespielt werden sollen, hilft der `concat`-Modus (zusammenfuehren). Zuerst eine Textdatei `liste.txt` erstellen:

```
file teil1.mp4
file teil2.mp4
```

Dann alles in eine Datei kopieren:

```
ffmpeg -f concat -safe 0 -i liste.txt -c copy komplett.mp4
```

`-c copy` kopiert die Daten unveraendert, also ohne erneutes Kodieren.

## 2. Tonspur sichern

Um nur den Ton aus einem Video zu speichern, eignet sich dieser Befehl:

```
ffmpeg -i video.mp4 -vn -acodec copy ton.mp3
```

`-vn` bedeutet "video none" (kein Bild). `-acodec copy` uebernimmt die Audiodaten ohne Aenderung.

## 3. Geschwindigkeit anpassen

Soll der Film schneller laufen, kann man die Zeitstempel (PTS = presentation time stamp) halbieren:

```
ffmpeg -i input.mp4 -filter:v "setpts=0.5*PTS" schnell.mp4
```

Der Faktor `0.5` fuehrt zu doppeltem Tempo.

## 4. Wasserzeichen einblenden

Ein Logo laesst sich mit dem Filter `overlay` (ueberblenden) platzieren:

```
ffmpeg -i video.mp4 -i logo.png -filter_complex "overlay=10:10" mit_logo.mp4
```

Die Werte `10:10` geben die Position in Pixeln von links oben an.


