import pytest

import videobatch_gui


def _make_window(monkeypatch, tmp_path):
    monkeypatch.setattr(
        videobatch_gui, "SETTINGS_FILE", tmp_path / "settings.ini"
    )
    monkeypatch.setattr(videobatch_gui, "check_ffmpeg", lambda: True)
    monkeypatch.setattr(
        videobatch_gui.QtWidgets.QMessageBox, "warning", lambda *args, **kwargs: None
    )
    return videobatch_gui.MainWindow()


def test_output_template_validation_resets_invalid(monkeypatch, tmp_path, qapp):
    window = _make_window(monkeypatch, tmp_path)
    window.output_template_edit.setText("{unbekannt}.mp4")

    window._validate_output_template()

    assert window.output_template_edit.text() == "{audio_stem}_{stamp}.mp4"


def test_project_dir_validation_falls_back_on_error(
    monkeypatch, tmp_path, qapp
):
    window = _make_window(monkeypatch, tmp_path)
    fallback = str(videobatch_gui.default_project_dir())

    def _fail_mkdir(self, parents=False, exist_ok=False):
        raise OSError("kein zugriff")

    monkeypatch.setattr(videobatch_gui.Path, "mkdir", _fail_mkdir)
    window.project_dir_edit.setText(str(tmp_path / "ungueltig"))

    window._validate_project_dir()

    assert window.project_dir_edit.text() == fallback
