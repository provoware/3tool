from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Signal

from core.gui_logic import format_human_size
from core.utils import human_time, probe_duration

MAX_PREVIEW_CACHE_ITEMS = 180
MIN_FONT_POINT_SIZE = 8
BASE_DIALOG_WIDTH_EM = 68
BASE_DIALOG_HEIGHT_EM = 42
BASE_PREVIEW_WIDTH_EM = 30
BASE_PREVIEW_HEIGHT_EM = 17
BASE_PREVIEW_MIN_HEIGHT_EM = 12
PREVIEW_MIN_SIDE_PX = 180
MIN_DIALOG_WIDTH_PX = 720
MIN_DIALOG_HEIGHT_PX = 520


def make_thumb(path: str, size: Tuple[int, int] = (160, 90)) -> QtGui.QPixmap:
    try:
        from PIL import Image

        img = Image.open(path)
        img.thumbnail(size)
        rgba_img = img.convert("RGBA") if img.mode != "RGBA" else img.copy()
        data = rgba_img.tobytes("raw", "RGBA")
        qimg = QtGui.QImage(
            data,
            rgba_img.size[0],
            rgba_img.size[1],
            QtGui.QImage.Format.Format_RGBA8888,
        )
        return QtGui.QPixmap.fromImage(qimg)
    except Exception:
        pix = QtGui.QPixmap(size[0], size[1])
        pix.fill(QtCore.Qt.GlobalColor.gray)
        return pix


class PreviewLabel(QtWidgets.QLabel):
    zoom_changed = Signal(float)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        if event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
            self.zoom_changed.emit(0.1 if event.angleDelta().y() > 0 else -0.1)
            event.accept()
            return
        super().wheelEvent(event)


class FilePickerDialog(QtWidgets.QDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        title: str,
        start_dir: Path,
        suffixes: Tuple[str, ...],
        mode: str,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self._base_preview_size = QtCore.QSize(640, 360)
        base_dialog_size = self._scaled_dialog_size()
        self.resize(base_dialog_size)
        self.setMinimumSize(self._scaled_minimum_dialog_size())
        self.setModal(True)
        self._suffixes = tuple(s.lower() for s in suffixes)
        self._mode = mode
        self._selection_order: List[str] = []
        self._zoom = 1.0
        self._audio_probe_cache: Dict[str, float] = {}
        self._image_preview_cache: Dict[str, QtGui.QPixmap] = {}
        self.current_dir = start_dir if start_dir.exists() else Path.home()

        root = QtWidgets.QVBoxLayout(self)
        header = QtWidgets.QHBoxLayout()
        self.path_edit = QtWidgets.QLineEdit(str(self.current_dir))
        btn_browse = QtWidgets.QPushButton("Ordner wechseln")
        btn_browse.clicked.connect(self._choose_directory)
        header.addWidget(QtWidgets.QLabel("Ordner:"))
        header.addWidget(self.path_edit, 1)
        header.addWidget(btn_browse)

        controls = QtWidgets.QHBoxLayout()
        self.sort_combo = QtWidgets.QComboBox()
        self.sort_combo.addItems(
            [
                "Auswahlreihenfolge",
                "Name A → Z",
                "Name Z → A",
                "Neueste zuerst",
                "Älteste zuerst",
                "Größte zuerst",
                "Kleinste zuerst",
            ]
        )
        self.sort_combo.currentTextChanged.connect(self._apply_sort)
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Filter (Dateiname)")
        self.search_edit.textChanged.connect(self._apply_filter)
        self.zoom_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(50, 250)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self._set_zoom_from_slider)
        controls.addWidget(QtWidgets.QLabel("Sortieren:"))
        controls.addWidget(self.sort_combo)
        controls.addWidget(QtWidgets.QLabel("Suche:"))
        controls.addWidget(self.search_edit, 1)
        controls.addWidget(QtWidgets.QLabel("Zoom:"))
        controls.addWidget(self.zoom_slider)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.file_list = QtWidgets.QTreeWidget()
        self.file_list.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.file_list.setHeaderLabels(["Auswahl", "Datei", "Größe"])
        self.file_list.setRootIsDecorated(False)
        self.file_list.itemChanged.connect(self._on_item_changed)
        self.file_list.currentItemChanged.connect(self._update_preview)
        self.file_list.installEventFilter(self)

        preview_wrap = QtWidgets.QWidget()
        preview_wrap.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        preview_layout = QtWidgets.QVBoxLayout(preview_wrap)
        self.preview_label = PreviewLabel("Vorschau")
        self.preview_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.preview_label.setMinimumHeight(
            self._scaled_length(BASE_PREVIEW_MIN_HEIGHT_EM, PREVIEW_MIN_SIDE_PX)
        )
        self.preview_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.preview_label.zoom_changed.connect(self._adjust_zoom)
        self.preview_info = QtWidgets.QPlainTextEdit()
        self.preview_info.setReadOnly(True)
        preview_layout.addWidget(self.preview_label, 1)
        preview_layout.addWidget(self.preview_info)

        splitter.addWidget(self.file_list)
        splitter.addWidget(preview_wrap)
        splitter.setChildrenCollapsible(False)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        footer = QtWidgets.QHBoxLayout()
        self.selected_label = QtWidgets.QLabel("0 ausgewählt")
        self.ok_button = QtWidgets.QPushButton("Auswahl übernehmen")
        self.ok_button.setEnabled(False)
        self.ok_button.clicked.connect(self.accept)
        cancel_button = QtWidgets.QPushButton("Abbrechen")
        cancel_button.clicked.connect(self.reject)
        footer.addWidget(self.selected_label)
        footer.addStretch(1)
        footer.addWidget(self.ok_button)
        footer.addWidget(cancel_button)

        root.addLayout(header)
        root.addLayout(controls)
        root.addWidget(splitter, 1)
        root.addLayout(footer)
        self._load_files()

    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if (
            obj is self.file_list
            and event.type() == QtCore.QEvent.Type.KeyPress
            and isinstance(event, QtGui.QKeyEvent)
            and event.key() == QtCore.Qt.Key.Key_Space
        ):
            item = self.file_list.currentItem()
            if item:
                item.setCheckState(
                    0,
                    (
                        QtCore.Qt.CheckState.Unchecked
                        if item.checkState(0) == QtCore.Qt.CheckState.Checked
                        else QtCore.Qt.CheckState.Checked
                    ),
                )
                return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        current_item = self.file_list.currentItem()
        if current_item is not None and self._mode != "audio":
            self._update_preview(current_item)

    def _choose_directory(self) -> None:
        selected = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Ordner wählen", self.path_edit.text().strip()
        )
        if selected:
            self.current_dir = Path(selected)
            self.path_edit.setText(selected)
            self._load_files()

    def _font_point_size(self) -> int:
        font = self.font()
        point_size = font.pointSize()
        if point_size <= 0:
            point_size = font.pixelSize()
        if point_size <= 0:
            point_size = MIN_FONT_POINT_SIZE
        return max(MIN_FONT_POINT_SIZE, point_size)

    def _dpi_scale(self) -> float:
        screen = self.screen() or QtWidgets.QApplication.primaryScreen()
        if screen is None:
            return 1.0
        screen_dpi = max(1.0, screen.logicalDotsPerInchX())
        return max(1.0, self.logicalDpiX() / screen_dpi)

    def _scaled_length(self, em_units: int, min_px: int = 1) -> int:
        em_int = em_units if isinstance(em_units, int) else 1
        em_int = max(1, em_int)
        return max(
            min_px, int(em_int * self._font_point_size() * self._dpi_scale())
        )

    def _scaled_dialog_size(self) -> QtCore.QSize:
        return QtCore.QSize(
            self._scaled_length(BASE_DIALOG_WIDTH_EM),
            self._scaled_length(BASE_DIALOG_HEIGHT_EM),
        )

    def _scaled_minimum_dialog_size(self) -> QtCore.QSize:
        return QtCore.QSize(
            self._scaled_length(48, MIN_DIALOG_WIDTH_PX),
            self._scaled_length(26, MIN_DIALOG_HEIGHT_PX),
        )

    def _update_base_preview_size(self) -> None:
        preview_rect = self.preview_label.contentsRect()
        fallback = QtCore.QSize(
            self._scaled_length(BASE_PREVIEW_WIDTH_EM, PREVIEW_MIN_SIDE_PX),
            self._scaled_length(BASE_PREVIEW_HEIGHT_EM, PREVIEW_MIN_SIDE_PX),
        )
        if preview_rect.width() <= 0 or preview_rect.height() <= 0:
            available_size = fallback
        else:
            available_size = preview_rect.size()
        width = max(PREVIEW_MIN_SIDE_PX, available_size.width())
        height = max(PREVIEW_MIN_SIDE_PX, available_size.height())
        self._base_preview_size = QtCore.QSize(width, height)

    def _load_files(self) -> None:
        entered = Path(self.path_edit.text().strip())
        if entered.exists() and entered.is_dir():
            self.current_dir = entered
        self.file_list.blockSignals(True)
        self.file_list.clear()
        for path in sorted(
            self.current_dir.iterdir(), key=lambda p: p.name.lower()
        ):
            if path.is_file() and path.suffix.lower() in self._suffixes:
                item = QtWidgets.QTreeWidgetItem(
                    ["", path.name, format_human_size(path)]
                )
                item.setData(0, QtCore.Qt.ItemDataRole.UserRole, str(path))
                item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
                self.file_list.addTopLevelItem(item)
        self.file_list.blockSignals(False)
        self._apply_filter()
        self._apply_sort()

    def _apply_filter(self) -> None:
        query = self.search_edit.text().strip().lower()
        for i in range(self.file_list.topLevelItemCount()):
            item = self.file_list.topLevelItem(i)
            if item is None:
                continue
            item.setHidden(query not in item.text(1).lower())

    def _apply_sort(self) -> None:
        mode = self.sort_combo.currentText()
        rows: List[QtWidgets.QTreeWidgetItem] = []
        for _ in range(self.file_list.topLevelItemCount()):
            row = self.file_list.takeTopLevelItem(0)
            if row is not None:
                rows.append(row)
        if mode == "Auswahlreihenfolge":
            rows.sort(
                key=lambda item: (
                    self._selection_order.index(
                        str(item.data(0, QtCore.Qt.ItemDataRole.UserRole))
                    )
                    if str(item.data(0, QtCore.Qt.ItemDataRole.UserRole))
                    in self._selection_order
                    else 99999
                )
            )
        else:
            reverse = mode in ("Name Z → A", "Neueste zuerst", "Größte zuerst")

            def _key_name(it: QtWidgets.QTreeWidgetItem) -> str:
                return it.text(1).lower()

            def _key_mtime(it: QtWidgets.QTreeWidgetItem) -> float:
                return (
                    Path(str(it.data(0, QtCore.Qt.ItemDataRole.UserRole)))
                    .stat()
                    .st_mtime
                )

            def _key_size(it: QtWidgets.QTreeWidgetItem) -> int:
                return (
                    Path(str(it.data(0, QtCore.Qt.ItemDataRole.UserRole)))
                    .stat()
                    .st_size
                )

            sort_key: Callable[[QtWidgets.QTreeWidgetItem], Any]
            if "Name" in mode:
                sort_key = _key_name
            elif "Neueste" in mode or "Älteste" in mode:
                sort_key = _key_mtime
            else:
                sort_key = _key_size

            rows.sort(key=sort_key, reverse=reverse)
        self.file_list.addTopLevelItems(rows)

    def _on_item_changed(self, item: QtWidgets.QTreeWidgetItem, _: int) -> None:
        path = str(item.data(0, QtCore.Qt.ItemDataRole.UserRole))
        if (
            item.checkState(0) == QtCore.Qt.CheckState.Checked
            and path not in self._selection_order
        ):
            self._selection_order.append(path)
        elif item.checkState(0) != QtCore.Qt.CheckState.Checked:
            self._selection_order = [
                p for p in self._selection_order if p != path
            ]
        count = len(self._selection_order)
        self.selected_label.setText(f"{count} ausgewählt")
        self.ok_button.setEnabled(count > 0)

    def _set_zoom_from_slider(self, value: int) -> None:
        self._zoom = max(0.5, min(2.5, value / 100))
        self._update_preview(self.file_list.currentItem())

    def _adjust_zoom(self, delta: float) -> None:
        self._zoom = max(0.5, min(2.5, self._zoom + delta))
        self.zoom_slider.setValue(int(self._zoom * 100))

    def _cache_image_preview(self, key: str, pixmap: QtGui.QPixmap) -> None:
        self._image_preview_cache[key] = pixmap
        if len(self._image_preview_cache) > MAX_PREVIEW_CACHE_ITEMS:
            self._image_preview_cache.pop(
                next(iter(self._image_preview_cache)), None
            )

    def _update_preview(
        self,
        current: Optional[QtWidgets.QTreeWidgetItem],
        _previous: Optional[QtWidgets.QTreeWidgetItem] = None,
    ) -> None:
        if not current:
            return
        path = Path(str(current.data(0, QtCore.Qt.ItemDataRole.UserRole)))
        info = [f"Datei: {path.name}", f"Pfad: {path}"]
        if self._mode == "audio":
            if str(path) not in self._audio_probe_cache:
                self._audio_probe_cache[str(path)] = probe_duration(str(path))
            info.append(
                f"Dauer: {human_time(max(0.0, self._audio_probe_cache[str(path)]))}"
            )
            self.preview_label.setText("Audio-Vorschau: Doppelklick in Liste")
            self.preview_label.setPixmap(QtGui.QPixmap())
        else:
            self._update_base_preview_size()
            if str(path) not in self._image_preview_cache:
                self._cache_image_preview(
                    str(path),
                    make_thumb(
                        str(path),
                        size=(
                            self._base_preview_size.width(),
                            self._base_preview_size.height(),
                        ),
                    ),
                )
            pix = self._image_preview_cache[str(path)]
            self.preview_label.setPixmap(
                pix.scaled(
                    int(self._base_preview_size.width() * self._zoom),
                    int(self._base_preview_size.height() * self._zoom),
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
            )
            self.preview_label.setText("")
        self.preview_info.setPlainText("\n".join(info))

    def selected_files(self) -> List[str]:
        return list(self._selection_order)
