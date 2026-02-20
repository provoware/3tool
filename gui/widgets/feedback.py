from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class ErrorBanner(QtWidgets.QFrame):
    """Sichtbarer Fehlerhinweis mit nächstem Schritt in einfacher Sprache."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("feedbackKind", "error")
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setVisible(False)
        self.setAccessibleName("Fehlerhinweis")
        self.setAccessibleDescription(
            "Zeigt kritische Fehler und einen klaren nächsten Schritt."
        )

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        self._icon = QtWidgets.QLabel("⚠")
        self._icon.setProperty("feedbackIcon", "true")
        self._text = QtWidgets.QLabel("")
        self._text.setWordWrap(True)
        self._text.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self._close_button = QtWidgets.QToolButton()
        self._close_button.setText("Ausblenden")
        self._close_button.clicked.connect(self.clear_message)

        layout.addWidget(self._icon, 0)
        layout.addWidget(self._text, 1)
        layout.addWidget(self._close_button, 0)

    def show_error(self, title: str, message: str) -> None:
        clean_title = " ".join((title or "Fehler").split())
        clean_msg = " ".join((message or "Bitte Hinweise prüfen.").split())
        self._text.setText(
            f"{clean_title}: {clean_msg} Nächster Schritt: Hinweise prüfen und erneut starten."
        )
        self.setVisible(True)

    def clear_message(self) -> None:
        self._text.setText("")
        self.setVisible(False)


class WarningBadge(QtWidgets.QLabel):
    """Kleine Warnmarke für nicht-kritische Hinweise."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("feedbackKind", "warning")
        self.setVisible(False)
        self.setWordWrap(True)
        self.setAccessibleName("Warnhinweis")

    def show_warning(self, message: str) -> None:
        clean_msg = " ".join((message or "Hinweis").split())
        self.setText(f"Hinweis: {clean_msg}")
        self.setVisible(True)

    def clear_warning(self) -> None:
        self.clear()
        self.setVisible(False)


class InlineValidationBadge(QtWidgets.QLabel):
    """Inline-Hinweis direkt am Eingabefeld (ok/warn) mit Tooltip."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setVisible(False)
        self.setWordWrap(True)
        self.setProperty("feedbackKind", "warning")

    def show_validation(self, is_valid: bool, message: str) -> None:
        clean_msg = " ".join((message or "").split())
        if not clean_msg:
            self.clear_validation()
            return
        prefix = "OK" if is_valid else "Prüfen"
        self.setProperty("feedbackKind", "success" if is_valid else "warning")
        self.setText(f"{prefix}: {clean_msg}")
        self.setToolTip(clean_msg)
        self.style().unpolish(self)
        self.style().polish(self)
        self.setVisible(True)

    def clear_validation(self) -> None:
        self.clear()
        self.setToolTip("")
        self.setVisible(False)


class SuccessToast(QtWidgets.QLabel):
    """Kurzlebige Erfolgs-/Statusmeldung im Hauptfenster."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("feedbackKind", "success")
        self.setVisible(False)
        self.setWordWrap(True)
        self.setAccessibleName("Erfolgs-Hinweis")
        self._hide_timer = QtCore.QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._hide_message)

    def show_message(self, message: str, timeout_ms: int = 3000) -> None:
        clean_msg = " ".join((message or "Fertig.").split())
        if not clean_msg:
            return
        self.setText(f"OK: {clean_msg}")
        self.setVisible(True)
        self._hide_timer.start(max(1200, int(timeout_ms)))

    def _hide_message(self) -> None:
        self.clear()
        self.setVisible(False)
