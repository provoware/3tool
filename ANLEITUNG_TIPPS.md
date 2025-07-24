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

## Weitere Befehle

Das Tool lässt sich auch komplett über die Kommandozeile nutzen:

```bash
python3 videobatch_extra.py --img bild.jpg --aud ton.mp3 --out output
```

Dieser Befehl erstellt ein einzelnes Video ohne die GUI.
