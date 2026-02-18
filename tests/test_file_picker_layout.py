from __future__ import annotations

from pathlib import Path

import pytest

QtCore = pytest.importorskip("PySide6.QtCore", exc_type=ImportError)
QtGui = pytest.importorskip("PySide6.QtGui", exc_type=ImportError)
QtWidgets = pytest.importorskip("PySide6.QtWidgets", exc_type=ImportError)

from gui.dialogs.file_picker import (  # noqa: E402
    PREVIEW_MIN_SIDE_PX,
    FilePickerDialog,
)


def _create_sample_image(target: Path) -> None:
    image = QtGui.QImage(640, 360, QtGui.QImage.Format_RGB32)
    image.fill(QtGui.QColor("#336699"))
    image.save(str(target))


def _build_dialog(tmp_path: Path, mode: str = "image") -> FilePickerDialog:
    image_path = tmp_path / "bild.png"
    _create_sample_image(image_path)
    return FilePickerDialog(
        parent=QtWidgets.QWidget(),
        title="Dateien",
        start_dir=tmp_path,
        suffixes=(".png",),
        mode=mode,
    )


def _is_inside(widget_rect, outer_rect) -> bool:
    return (
        widget_rect.left() >= outer_rect.left()
        and widget_rect.right() <= outer_rect.right()
        and widget_rect.top() >= outer_rect.top()
        and widget_rect.bottom() <= outer_rect.bottom()
    )


def test_file_picker_keeps_core_controls_visible_on_small_width(
    qapp, qtbot, tmp_path
):
    dialog = _build_dialog(tmp_path)
    qtbot.addWidget(dialog)

    dialog.resize(760, 560)
    dialog.show()
    qtbot.waitForWindowShown(dialog)
    qapp.processEvents()

    target_rect = dialog.rect().adjusted(0, 0, -1, -1)
    for widget in (
        dialog.path_edit,
        dialog.sort_combo,
        dialog.search_edit,
        dialog.zoom_slider,
        dialog.file_list,
        dialog.preview_label,
        dialog.ok_button,
    ):
        assert widget.isVisible()
        assert _is_inside(widget.geometry(), target_rect)


def test_file_picker_scales_preview_base_size_with_high_dpi(
    qapp, qtbot, tmp_path, monkeypatch
):
    monkeypatch.setattr(FilePickerDialog, "_dpi_scale", lambda self: 2.0)
    dialog = _build_dialog(tmp_path)
    qtbot.addWidget(dialog)

    dialog.show()
    qtbot.waitForWindowShown(dialog)
    qapp.processEvents()

    item = dialog.file_list.topLevelItem(0)
    assert item is not None
    dialog.file_list.setCurrentItem(item)
    dialog._update_preview(item)

    initial_base_width = dialog._base_preview_size.width()
    assert initial_base_width >= PREVIEW_MIN_SIDE_PX
    assert dialog.preview_label.pixmap() is not None

    dialog.resize(560, 480)
    qapp.processEvents()
    resized_base_width = dialog._base_preview_size.width()
    assert resized_base_width >= PREVIEW_MIN_SIDE_PX
    assert resized_base_width <= initial_base_width
