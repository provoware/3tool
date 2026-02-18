from __future__ import annotations

import logging
from typing import Dict, List, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from core.gui_logic import (
    clamp_progress,
    parse_non_negative_int,
    resolve_dashboard_columns,
)
from core.ui_texts import text_with_fallback

logger = logging.getLogger("VideoBatchTool")


class InfoDashboard(QtWidgets.QWidget):
    def __init__(self, texts: Optional[Dict[str, str]] = None):
        super().__init__()
        self.texts = texts or {}
        self._metric_cards: List[QtWidgets.QFrame] = []
        self.total_label = QtWidgets.QLabel("0")
        self.total_label.setAccessibleName("Gesamtzahl")
        self.done_label = QtWidgets.QLabel("0")
        self.done_label.setAccessibleName("Fertig")
        self.err_label = QtWidgets.QLabel("0")
        self.err_label.setAccessibleName("Fehler")
        self.selected_images_label = QtWidgets.QLabel("0")
        self.selected_images_label.setAccessibleName("Ausgewählte Bilder")
        self.selected_audios_label = QtWidgets.QLabel("0")
        self.selected_audios_label.setAccessibleName("Ausgewählte Audios")
        self.ffmpeg_lbl = QtWidgets.QLabel("ffmpeg: ?")
        self.env_lbl = QtWidgets.QLabel("Env: OK")
        self.progress_value = QtWidgets.QLabel("0%")
        self.progress_value.setProperty("metricValue", True)
        self.progress = QtWidgets.QProgressBar()
        self.progress.setMinimumHeight(28)
        self.progress.setFormat("%p%")
        self.mini_log = QtWidgets.QPlainTextEdit()
        self.mini_log.setReadOnly(True)
        self.mini_log.setMaximumBlockCount(300)
        self.mini_log.setMinimumHeight(96)

        summary = QtWidgets.QLabel(
            text_with_fallback(
                self.texts, "dashboard.summary", "Datei-Übersicht"
            )
        )
        summary.setObjectName("DashboardSummary")
        summary.setStyleSheet("font-weight: 700;")

        self.selection_label = QtWidgets.QLabel()

        self.cards_layout = QtWidgets.QGridLayout()
        self.cards_layout.setSpacing(8)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self._metric_cards.extend(
            [
                self._build_metric_card(
                    text_with_fallback(
                        self.texts, "dashboard.counts.total", "Gesamt"
                    ),
                    self.total_label,
                ),
                self._build_metric_card(
                    text_with_fallback(
                        self.texts, "dashboard.counts.done", "Fertig"
                    ),
                    self.done_label,
                ),
                self._build_metric_card(
                    text_with_fallback(
                        self.texts, "dashboard.counts.errors", "Fehler"
                    ),
                    self.err_label,
                ),
                self._build_metric_card(
                    text_with_fallback(
                        self.texts, "dashboard.counts.progress", "Fortschritt"
                    ),
                    self.progress_value,
                ),
                self._build_metric_card(
                    text_with_fallback(
                        self.texts, "dashboard.counts.images", "Bilder"
                    ),
                    self.selected_images_label,
                ),
                self._build_metric_card(
                    text_with_fallback(
                        self.texts, "dashboard.counts.audios", "Audios"
                    ),
                    self.selected_audios_label,
                ),
            ]
        )
        self._reflow_metric_cards(self.width())

        status_row = QtWidgets.QHBoxLayout()
        status_row.setSpacing(10)
        status_row.addWidget(self.progress, 2)
        status_row.addWidget(self.ffmpeg_lbl, 1)
        status_row.addWidget(self.env_lbl, 1)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(8)
        lay.addWidget(summary)
        lay.addWidget(self.selection_label)
        lay.addLayout(self.cards_layout)
        lay.addLayout(status_row)
        lay.addWidget(self.mini_log)
        self.set_selection_counts(0, 0)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._reflow_metric_cards(event.size().width())

    def _reflow_metric_cards(self, available_width: object) -> None:
        columns = resolve_dashboard_columns(available_width)
        while self.cards_layout.count() > 0:
            self.cards_layout.takeAt(0)
        for index, card in enumerate(self._metric_cards):
            self.cards_layout.addWidget(card, index // columns, index % columns)

    def _build_metric_card(
        self, title: str, value_label: QtWidgets.QLabel
    ) -> QtWidgets.QFrame:
        title_label = QtWidgets.QLabel(title)
        title_label.setProperty("metricLabel", True)
        value_label.setProperty("metricValue", True)
        value_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )

        card = QtWidgets.QFrame()
        card.setProperty("dashboardCard", True)
        card.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        lay = QtWidgets.QVBoxLayout(card)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(2)
        lay.addWidget(title_label)
        lay.addWidget(value_label)
        return card

    def set_counts(self, t: object, d: object, e: object) -> None:
        total = parse_non_negative_int(t, "gesamt")
        done = min(parse_non_negative_int(d, "fertig"), total)
        errors = min(parse_non_negative_int(e, "fehler"), total)
        self.total_label.setText(str(total))
        self.done_label.setText(str(done))
        self.err_label.setText(str(errors))

    def set_selection_counts(
        self, selected_images: int, selected_audios: int
    ) -> None:
        valid_images = parse_non_negative_int(
            selected_images, "ausgewaehlte Bilder"
        )
        valid_audios = parse_non_negative_int(
            selected_audios, "ausgewaehlte Audios"
        )
        self.selected_images_label.setText(str(valid_images))
        self.selected_audios_label.setText(str(valid_audios))
        template = text_with_fallback(
            self.texts,
            "dashboard.selection",
            "Auswahl: {selected_images} Bilder, {selected_audios} Audios",
        )
        self.selection_label.setText(
            template.format(
                selected_images=valid_images, selected_audios=valid_audios
            )
        )

    def set_progress(self, v: object) -> None:
        progress = clamp_progress(v)
        self.progress.setValue(progress)
        self.progress_value.setText(f"{progress}%")

    def set_env(self, ff_ok: bool, imp_ok: bool = True) -> None:
        self.ffmpeg_lbl.setText(
            text_with_fallback(
                self.texts,
                (
                    "dashboard.status.ffmpeg_ok"
                    if ff_ok
                    else "dashboard.status.ffmpeg_missing"
                ),
                "ffmpeg: OK" if ff_ok else "ffmpeg: FEHLT",
            )
        )
        self.env_lbl.setText(
            text_with_fallback(
                self.texts,
                (
                    "dashboard.status.env_ok"
                    if imp_ok
                    else "dashboard.status.env_missing"
                ),
                "Umgebung: OK" if imp_ok else "Umgebung: FEHLT",
            )
        )

    def log(self, msg: str) -> None:
        self.mini_log.appendPlainText(str(msg))
