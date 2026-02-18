import json
import logging
from pathlib import Path

import pytest

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


def test_text_with_format_formats_template() -> None:
    value = ui_texts.text_with_format(
        {"a.b": "Hallo {name}"},
        "a.b",
        "Fallback {name}",
        name="Welt",
    )
    assert value == "Hallo Welt"


def test_text_with_format_raises_for_missing_field() -> None:
    with pytest.raises(ValueError):
        ui_texts.text_with_format(
            {"a.b": "Hallo {name}"}, "a.b", "Fallback", other="X"
        )


def test_videobatch_gui_has_no_new_hardcoded_ui_tooltips_or_status_texts() -> (
    None
):
    source = Path("videobatch_gui.py").read_text(encoding="utf-8")

    forbidden_patterns = [
        '.setToolTip("',
        'statusBar().showMessage("',
        'QMessageBox.information(self, "',
        'QMessageBox.warning(self, "',
        'QMessageBox.critical(self, "',
    ]

    for pattern in forbidden_patterns:
        assert pattern not in source, (
            "Neue UI-Texte dürfen nicht hartkodiert werden. "
            "Bitte Schlüssel in data/texts/v1/* anlegen und text_with_fallback nutzen. "
            f"Gefundenes Muster: {pattern}"
        )


def test_videobatch_gui_does_not_show_internal_dashboard_header_name() -> None:
    source = Path("videobatch_gui.py").read_text(encoding="utf-8")

    assert 'QGroupBox("DashboardHeader")' not in source, (
        "Interne Objekt-/Debug-Namen dürfen nicht als sichtbarer UI-Text erscheinen. "
        "Bitte Textschlüssel in data/texts/v1/* verwenden."
    )
