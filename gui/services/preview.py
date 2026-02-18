from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtMultimedia


def play_audio_preview(
    player: QtMultimedia.QMediaPlayer, path: str
) -> tuple[bool, str]:
    if not path:
        return False, "Leerpfad"
    file_path = Path(path)
    if not file_path.exists():
        return False, f"Die Audiodatei wurde nicht gefunden: {file_path}"
    player.setSource(QtCore.QUrl.fromLocalFile(str(file_path)))
    player.play()
    return True, file_path.name


def stop_audio_preview(player: QtMultimedia.QMediaPlayer) -> bool:
    if (
        player.playbackState()
        == QtMultimedia.QMediaPlayer.PlaybackState.StoppedState
    ):
        return False
    player.stop()
    return True
