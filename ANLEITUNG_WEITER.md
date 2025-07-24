# Weiterführende Tipps

Diese Hinweise bauen auf den bisherigen Anleitungen auf und richten sich an Laien, die mehr ausprobieren möchten. Fachbegriffe stehen in Klammern und werden kurz erklärt.

## 1. Mehrere Videos automatisch erzeugen

Im Ordner `samples` befinden sich Beispielbilder und Audiodateien. Man kann sie per Schleife ("loop" – eine wiederholte Ausführung) verarbeiten:

```bash
for img in samples/*.jpg; do
    aud="${img%.jpg}.mp3"
    python3 videobatch_extra.py --img "$img" --aud "$aud" --out output
done
```

Hier wird `videobatch_extra.py` (die Kommandozeilenversion) für jedes Bild aufgerufen.

## 2. Ausgabeordner anpassen

Standardmäßig landen fertige Videos im Unterordner `VideoBatchTool_Out`. Wer einen anderen Pfad nutzen möchte, trägt ihn im Feld "Ausgabeordner" ein oder startet das Skript so:

```bash
python3 videobatch_extra.py --img bild.jpg --aud ton.mp3 --out /pfad/zum/ziel
```

## 3. Qualität einstellen

Die Option `--crf` bestimmt die Videoqualität. Niedrige Werte bedeuten höhere Qualität (und größere Dateien). Beispiel:

```bash
python3 videobatch_extra.py --img bild.jpg --aud ton.mp3 --crf 18
```

`crf` steht für "Constant Rate Factor" (konstanter Qualitätsfaktor).

## 4. Fehlersuche

Falls etwas nicht funktioniert, hilft die Logdatei weiter. Über das Menü "Hilfe" lässt sich "Logdatei öffnen" anklicken. Dort stehen weitere Details.

