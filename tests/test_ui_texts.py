import json
import logging
from pathlib import Path

from core import ui_texts


def test_load_ui_texts_returns_empty_when_file_missing(
    tmp_path: Path, monkeypatch
) -> None:
    logger = logging.getLogger("test_ui_texts_missing")
    monkeypatch.setattr(ui_texts, "TEXT_ARCHIVE_DIR", tmp_path)

    texts = ui_texts.load_ui_texts(logger=logger, locale="de", version="v1")

    assert texts == {}


def test_load_ui_texts_returns_empty_for_invalid_json(
    tmp_path: Path, monkeypatch
) -> None:
    archive = tmp_path / "v1"
    archive.mkdir(parents=True)
    (archive / "de.json").write_text("{invalid", encoding="utf-8")
    monkeypatch.setattr(ui_texts, "TEXT_ARCHIVE_DIR", tmp_path)

    texts = ui_texts.load_ui_texts(locale="de", version="v1")

    assert texts == {}


def test_load_ui_texts_flattens_nested_json(
    tmp_path: Path, monkeypatch
) -> None:
    archive = tmp_path / "v1"
    archive.mkdir(parents=True)
    payload = {"menu": {"file": "Datei"}, "title": "Titel"}
    (archive / "de.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(ui_texts, "TEXT_ARCHIVE_DIR", tmp_path)

    texts = ui_texts.load_ui_texts(locale="de", version="v1")

    assert texts["menu.file"] == "Datei"
    assert texts["title"] == "Titel"
