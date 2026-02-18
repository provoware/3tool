from pathlib import Path

from gui.services.project_io import (
    build_project_payload,
    make_project_relative,
    resolve_project_path,
)


class _Pair:
    def __init__(self, image: str, audio: str, output: str) -> None:
        self.image_path = image
        self.audio_path = audio
        self.output = output


def test_make_project_relative_inside_root(tmp_path: Path) -> None:
    root = tmp_path
    nested = root / "a" / "b.txt"
    nested.parent.mkdir(parents=True)
    nested.write_text("x", encoding="utf-8")

    assert make_project_relative(str(nested), root) == "a/b.txt"


def test_resolve_project_path_uses_project_file_parent(tmp_path: Path) -> None:
    project_file = tmp_path / "project.json"
    result = resolve_project_path("media/a.mp3", None, project_file)
    assert result == str(tmp_path / "media" / "a.mp3")


def test_build_project_payload_has_relative_paths(tmp_path: Path) -> None:
    root = tmp_path
    image = root / "img.png"
    audio = root / "aud.mp3"
    output = root / "out.mp4"
    pairs = [_Pair(str(image), str(audio), str(output))]

    payload = build_project_payload(pairs, {"mode": "Video"}, root)
    assert payload["pairs"][0]["image"] == "img.png"
    assert payload["settings"]["mode"] == "Video"
