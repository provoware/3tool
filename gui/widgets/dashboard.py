from __future__ import annotations

import logging
from typing import Dict, List, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from core.gui_logic import (clamp_progress, parse_non_negative_int,
                            resolve_dashboard_columns)
from core.ui_texts import text_with_fallback

logger = logging.getLogger("VideoBatchTool")


class InfoDashboard(QtWidgets.QWidget):
    cardActivated = QtCore.Signal(str)

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
        self._status_cards: Dict[str, QtWidgets.QPushButton] = {}

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
        self._refresh_metric_card_sizes()

        self.status_cards_layout = QtWidgets.QGridLayout()
        self.status_cards_layout.setSpacing(8)
        self.status_cards_layout.setContentsMargins(0, 0, 0, 0)
        self._status_cards = self._build_status_cards()
        self._reflow_status_cards(self.width())

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
        lay.addLayout(self.status_cards_layout)
        lay.addLayout(status_row)
        lay.addWidget(self.mini_log)
        self.set_selection_counts(0, 0)
        self.set_quick_status(
            image_count=0,
            audio_count=0,
            pair_count=0,
            ffmpeg_ok=False,
            output_ready=False,
        )

    def changeEvent(self, event: QtCore.QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.FontChange:
            self._refresh_metric_card_sizes()
            self._reflow_metric_cards(self.width())

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._reflow_metric_cards(event.size().width())
        self._reflow_status_cards(event.size().width())

    def _reflow_metric_cards(self, available_width: object) -> None:
        columns = resolve_dashboard_columns(available_width)
        while self.cards_layout.count() > 0:
            self.cards_layout.takeAt(0)
        for index, card in enumerate(self._metric_cards):
            self.cards_layout.addWidget(card, index // columns, index % columns)
        for index in range(columns):
            self.cards_layout.setColumnStretch(index, 1)

    def _build_metric_card(
        self, title: str, value_label: QtWidgets.QLabel
    ) -> QtWidgets.QFrame:
        title_label = QtWidgets.QLabel(title)
        title_label.setProperty("metricLabel", True)
        title_label.setWordWrap(True)
        value_label.setProperty("metricValue", True)
        value_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        value_label.setMinimumWidth(0)

        card = QtWidgets.QFrame()
        card.setProperty("dashboardCard", True)
        card.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        lay = QtWidgets.QVBoxLayout(card)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(4)
        lay.addWidget(title_label)
        lay.addWidget(value_label)
        return card

    def _build_status_cards(self) -> Dict[str, QtWidgets.QPushButton]:
        definitions = (
            ("images", "🖼 Bilder", "Noch keine Bilder gewählt"),
            ("audios", "🎵 Audios", "Noch keine Audios gewählt"),
            ("pairs", "🔗 Paare", "Noch keine Paare erstellt"),
            ("ffmpeg", "🧰 FFmpeg", "Prüfung steht aus"),
            ("output", "📁 Zielordner", "Zielordner prüfen"),
        )
        cards: Dict[str, QtWidgets.QPushButton] = {}
        for key, title, initial in definitions:
            button = QtWidgets.QPushButton(f"{title}\n{initial}")
            button.setProperty("dashboardStatusCard", True)
            button.setProperty("statusState", "warn")
            button.setAccessibleName(f"Dashboard-Karte {title}")
            button.setToolTip(
                "Klicken oder Enter drücken, um direkt zum passenden Bereich zu springen."
            )
            button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda _=False, card_key=key: self.cardActivated.emit(card_key)
            )
            button.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Preferred,
            )
            cards[key] = button
        return cards

    def _reflow_status_cards(self, available_width: object) -> None:
        columns = 1
        if isinstance(available_width, (int, float)):
            if available_width >= 900:
                columns = 5
            elif available_width >= 620:
                columns = 3
            elif available_width >= 420:
                columns = 2
        while self.status_cards_layout.count() > 0:
            self.status_cards_layout.takeAt(0)
        card_list = list(self._status_cards.values())
        for index, card in enumerate(card_list):
            self.status_cards_layout.addWidget(
                card, index // columns, index % columns
            )
        for index in range(columns):
            self.status_cards_layout.setColumnStretch(index, 1)

    def set_quick_status(
        self,
        image_count: object,
        audio_count: object,
        pair_count: object,
        ffmpeg_ok: bool,
        output_ready: bool,
    ) -> None:
        images = parse_non_negative_int(image_count, "bilder")
        audios = parse_non_negative_int(audio_count, "audios")
        pairs = parse_non_negative_int(pair_count, "paare")
        self._set_status_card(
            "images",
            "🖼 Bilder",
            f"{images} bereit" if images else "Noch keine Bilder gewählt",
            ok=images > 0,
        )
        self._set_status_card(
            "audios",
            "🎵 Audios",
            f"{audios} bereit" if audios else "Noch keine Audios gewählt",
            ok=audios > 0,
        )
        self._set_status_card(
            "pairs",
            "🔗 Paare",
            f"{pairs} nutzbar" if pairs else "Noch keine Paare erstellt",
            ok=pairs > 0,
        )
        self._set_status_card(
            "ffmpeg",
            "🧰 FFmpeg",
            "Installiert" if ffmpeg_ok else "Fehlt oder nicht erreichbar",
            ok=ffmpeg_ok,
        )
        self._set_status_card(
            "output",
            "📁 Zielordner",
            "Ordner ist bereit" if output_ready else "Bitte Zielordner prüfen",
            ok=output_ready,
        )

    def _set_status_card(
        self, key: str, title: str, description: str, ok: bool
    ) -> None:
        card = self._status_cards.get(key)
        if card is None:
            return
        icon = "🟢" if ok else "🟠"
        card.setText(f"{title}\n{icon} {description}")
        card.setProperty("statusState", "ok" if ok else "warn")
        card.style().unpolish(card)
        card.style().polish(card)

    def _refresh_metric_card_sizes(self) -> None:
        metric_height = QtGui.QFontMetrics(self.progress_value.font()).height()
        label_height = QtGui.QFontMetrics(self.selection_label.font()).height()
        card_min_height = max(76, metric_height + label_height + 24)
        for card in self._metric_cards:
            card.setMinimumHeight(card_min_height)

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
