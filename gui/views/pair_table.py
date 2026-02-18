from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QAbstractTableModel, QModelIndex

from core.media_validation import validate_media_pair
from core.utils import human_time, probe_duration
from gui.dialogs.file_picker import make_thumb
from gui.views.table_columns import COLUMNS


@dataclass
class PairItem:
    image_path: str
    audio_path: Optional[str] = None
    duration: float = 0.0
    output: str = ""
    status: str = "WARTET"
    progress: float = 0.0
    thumb: Optional[QtGui.QPixmap] = field(default=None, repr=False)
    valid: bool = True
    validation_msg: str = ""

    def update_duration(self) -> None:
        if self.audio_path:
            self.duration = probe_duration(self.audio_path)

    def load_thumb(self) -> None:
        if self.thumb is None and self.image_path:
            self.thumb = make_thumb(self.image_path)

    def validate(self) -> None:
        result = validate_media_pair(self.image_path, self.audio_path)
        self.valid = result.valid
        self.validation_msg = result.message


class PairTableModel(QAbstractTableModel):
    def __init__(self, pairs: List[PairItem]):
        super().__init__()
        self.pairs = pairs

    def rowCount(self, parent=QModelIndex()):
        return len(self.pairs)

    def columnCount(self, parent=QModelIndex()):
        return len(COLUMNS)

    def headerData(
        self,
        section,
        orientation,
        role=QtCore.Qt.ItemDataRole.DisplayRole,
    ):
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return None
        return (
            COLUMNS[section]
            if orientation == QtCore.Qt.Orientation.Horizontal
            else str(section + 1)
        )

    def data(self, idx, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not idx.isValid():
            return None
        item = self.pairs[idx.row()]
        col = idx.column()
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return str(idx.row() + 1)
            if col == 2:
                return item.image_path
            if col == 3:
                return item.audio_path or "—"
            if col == 4:
                return human_time(item.duration) if item.duration else "?"
            if col == 5:
                return item.output or "—"
            if col == 6:
                return f"{int(item.progress)}%"
            if col == 7:
                return item.status
        if role == QtCore.Qt.ItemDataRole.DecorationRole and col == 1:
            item.load_thumb()
            return item.thumb
        if role == QtCore.Qt.ItemDataRole.ToolTipRole:
            if col in (2, 3, 5):
                return {
                    2: item.image_path,
                    3: item.audio_path or "",
                    5: item.output or "",
                }[col]
            if not item.valid:
                return item.validation_msg
        if role == QtCore.Qt.ItemDataRole.ForegroundRole and not item.valid:
            return QtGui.QBrush(QtCore.Qt.GlobalColor.red)
        return None

    def flags(self, idx):
        if not idx.isValid():
            return QtCore.Qt.ItemFlag.NoItemFlags
        base = (
            QtCore.Qt.ItemFlag.ItemIsEnabled
            | QtCore.Qt.ItemFlag.ItemIsSelectable
        )
        if idx.column() in (2, 3, 5):
            base |= QtCore.Qt.ItemFlag.ItemIsEditable
        return base

    def setData(self, idx, value, role=QtCore.Qt.ItemDataRole.EditRole):
        if role != QtCore.Qt.ItemDataRole.EditRole or not idx.isValid():
            return False
        item = self.pairs[idx.row()]
        col = idx.column()
        if col == 2:
            item.image_path = value
            item.thumb = None
        elif col == 3:
            item.audio_path = value
            item.update_duration()
        elif col == 5:
            item.output = value
        else:
            return False
        item.validate()
        self.dataChanged.emit(idx, idx)
        return True

    def add_pairs(self, new_pairs: List[PairItem]) -> None:
        self.beginInsertRows(
            QModelIndex(), len(self.pairs), len(self.pairs) + len(new_pairs) - 1
        )
        self.pairs.extend(new_pairs)
        self.endInsertRows()

    def remove_rows(self, rows: List[int]) -> None:
        for row in sorted(rows, reverse=True):
            if 0 <= row < len(self.pairs):
                self.beginRemoveRows(QModelIndex(), row, row)
                self.pairs.pop(row)
                self.endRemoveRows()

    def clear(self) -> None:
        self.beginResetModel()
        self.pairs.clear()
        self.endResetModel()
