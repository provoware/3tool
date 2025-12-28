# =========================================
# QUICKSTART
# Start (alles automatisch):   python3 videobatch_launcher.py
# Edit mit micro:              micro videobatch_launcher.py
# Venv löschen (Reset):        rm -rf .videotool_env
# =========================================

from __future__ import annotations
import logging
import shutil
import subprocess as sp
import sys
import os
import shutil
import subprocess as sp
from pathlib import Path
import shutil
import subprocess

from core import launcher_checks
from core.paths import log_dir, user_data_dir

ENV_DIR = launcher_checks.ENV_DIR
SELF = Path(__file__).resolve()
FLAG = "VT_BOOTSTRAPPED"
USER_DATA_DIR = user_data_dir()
LOG_FILE = log_dir() / "launcher.log"


def setup_logging(debug: bool) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if debug else logging.INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    if not any(
        isinstance(handler, logging.FileHandler)
        and handler.baseFilename == str(LOG_FILE)
        for handler in root_logger.handlers
    ):
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        root_logger.addHandler(handler)


def reboot_into_venv():
    py_path = Path(launcher_checks.venv_python())
    if not py_path.exists():
        try:
            launcher_checks.ensure_venv()
        except Exception as e:
            print("Konnte virtuelle Umgebung nicht erstellen:", e)
            py_path = Path(sys.executable)
        else:
            path_obj = (
                ENV_DIR / ("Scripts" if os.name == "nt" else "bin") / "python"
            )
            py_path = (
                Path(launcher_checks.venv_python())
                if path_obj.exists()
                else Path(sys.executable)
            )

    env = os.environ.copy()
    env[FLAG] = "1"
    try:
        os.execvpe(str(py_path), [str(py_path), str(SELF)], env)
    except FileNotFoundError:
        print("Python-Interpreter nicht gefunden:", py_path)
        os.execvpe(sys.executable, [sys.executable, str(SELF)], env)


def bootstrap_console():
    if not launcher_checks.in_venv():
        launcher_checks.ensure_venv()
        reboot_into_venv()
    elif ENV_DIR.exists() and os.environ.get(FLAG) != "1":
        reboot_into_venv()

    py = str(launcher_checks.venv_python())
    if not launcher_checks.pip_show(py, "PySide6"):
        launcher_checks.pip_install(py, ["PySide6"])


def build_wizard():
    from PySide6 import QtCore, QtGui, QtWidgets

    class CheckWorker(QtCore.QThread):
        results_ready = QtCore.Signal(list)
        failed = QtCore.Signal(str)

        def run(self):
            try:
                results = launcher_checks.collect_checks(
                    str(launcher_checks.venv_python()), Path.cwd()
                )
            except Exception as exc:
                self.failed.emit(str(exc))
            else:
                self.results_ready.emit(results)

    class FixWorker(QtCore.QThread):
        results_ready = QtCore.Signal(list)
        failed = QtCore.Signal(str)

        def run(self):
            try:
                results = launcher_checks.run_repairs(
                    str(launcher_checks.venv_python()), Path.cwd()
                )
            except Exception as exc:
                self.failed.emit(str(exc))
            else:
                self.results_ready.emit(results)

    class InstallWorker(QtCore.QThread):
        progress = QtCore.Signal(int, str)
        finished = QtCore.Signal(object)

        def __init__(self, py: str, missing_pkgs: list[str], ffmpeg_ok: bool):
            super().__init__()
            self.py = py
            self.missing_pkgs = list(missing_pkgs)
            self.ffmpeg_ok = ffmpeg_ok

        def run(self):
            errors = []
            self.progress.emit(5, "Installationsprüfung startet…")

            if self.missing_pkgs:
                self.progress.emit(15, "Python-Pakete werden installiert…")
                try:
                    launcher_checks.pip_install(self.py, self.missing_pkgs)
                except Exception as e:
                    errors.append(
                        {
                            "title": "Pakete konnten nicht installiert werden",
                            "message": (
                                "Bitte pruefe deine Internetverbindung und "
                                "die Schreibrechte im Projektordner."
                            ),
                            "details": str(e),
                            "permission": False,
                        }
                    )

            self.progress.emit(45, "Pruefe ffmpeg/ffprobe…")
            self.ffmpeg_ok = bool(
                shutil.which("ffmpeg") and shutil.which("ffprobe")
            )
            if not self.ffmpeg_ok and sys.platform.startswith("linux"):
                manager = launcher_checks.linux_package_manager()
                if not manager:
                self.progress.emit(
                    60,
                    "ffmpeg wird installiert (Administratorrechte erforderlich)…",
                )
                try:
                    subprocess.check_call(["sudo", "apt", "update"])
                    subprocess.check_call(["sudo", "apt", "install", "-y", "ffmpeg"])
                except Exception as e:
                    errors.append(
                        {
                            "title": "Kein Paketmanager erkannt",
                            "message": (
                                "Deine Linux-Distribution wurde nicht erkannt. "
                                "Bitte installiere ffmpeg manuell."
                            ),
                            "details": launcher_checks.ffmpeg_install_hint(),
                            "permission": False,
                        }
                    )
                else:
                    self.progress.emit(
                        60,
                        (
                            "ffmpeg wird installiert (Administratorrechte "
                            "erforderlich)…"
                        ),
                    )
                    try:
                        if manager.update_cmd:
                            sp.check_call(manager.update_cmd)
                        sp.check_call(manager.install_cmd)
                    except sp.CalledProcessError as e:
                        errors.append(
                            {
                                "title": "Administratorrechte fehlen",
                                "message": (
                                    "Die automatische Installation braucht "
                                    "Administratorrechte (Admin-Rechte). "
                                    "Bitte starte das Programm mit passenden "
                                    "Rechten oder installiere ffmpeg manuell."
                                ),
                                "details": (
                                    f"{manager.name}: "
                                    f"{launcher_checks.format_command(manager.install_cmd)} "
                                    f"({e})"
                                ),
                                "permission": True,
                            }
                        )
                    except FileNotFoundError as e:
                        errors.append(
                            {
                                "title": "Paketmanager nicht gefunden",
                                "message": (
                                    "Der Paketmanager-Befehl ist nicht "
                                    "verfügbar. Bitte installiere ffmpeg "
                                    "manuell."
                                ),
                                "details": str(e),
                                "permission": False,
                            }
                        )

            self.progress.emit(85, "Abschlusspruefung laeuft…")
            missing_after = [
                p
                for p in launcher_checks.REQ_PKGS
                p for p in launcher_checks.REQ_PKGS
                if not launcher_checks.pip_show(self.py, p)
            ]
            ffmpeg_after = bool(
                shutil.which("ffmpeg") and shutil.which("ffprobe")
            )
            self.progress.emit(100, "Fertig.")
            self.finished.emit(
                {
                    "missing_pkgs": missing_after,
                    "ffmpeg_ok": ffmpeg_after,
                    "errors": errors,
                }
            )

    class Wizard(QtWidgets.QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("VideoBatchTool – Setup")
            self.resize(700, 520)
            self._debug_enabled = os.environ.get("VT_DEBUG") == "1"
            self.resize(600, 420)
            self.py = str(launcher_checks.venv_python())
            self._build_ui()
            self._start_check()

        def _build_ui(self):
            self.info = QtWidgets.QTextBrowser()
            self.info.setOpenExternalLinks(True)
            self.info.setAccessibleName("Info-Text")
            self.info.setAccessibleDescription(
                "Status- und Hilfeinformationen zur Installation und Prüfung."
            )
            self.progress = QtWidgets.QProgressBar(maximum=100)
            self.progress.setAccessibleName("Fortschritt")
            self.progress.setAccessibleDescription(
                "Zeigt den Fortschritt der Prüf- und Reparaturschritte."
            )
            self.status_label = QtWidgets.QLabel("Bereit.")

            self.theme_label = QtWidgets.QLabel("&Farbschema (Theme):")
            self.theme_select = QtWidgets.QComboBox()
            self.theme_select.addItems(["Hell", "Dunkel", "Hoher Kontrast"])
            self.theme_select.currentTextChanged.connect(self._apply_theme)
            self.theme_label.setBuddy(self.theme_select)
            self.theme_select.setAccessibleName("Farbschema")
            self.theme_select.setAccessibleDescription(
                "Wählen Sie das Farbschema für den Launcher."
            )

            self.debug_check = QtWidgets.QCheckBox("&Debug-Log (Fehlersuche)")
            self.debug_check.setChecked(self._debug_enabled)
            self.debug_check.toggled.connect(self._toggle_debug)
            self.debug_check.setAccessibleName("Debug-Log")
            self.debug_check.setAccessibleDescription(
                "Schaltet die ausführliche Protokollierung für die Fehlersuche ein."
            )

            self.btn_fix = QtWidgets.QPushButton("&Reparieren")
            self.btn_start = QtWidgets.QPushButton("&Starten →")
            self.btn_exit = QtWidgets.QPushButton("B&eenden")
            self.btn_fix.setAccessibleName("Reparieren")
            self.btn_fix.setAccessibleDescription(
                "Startet die automatische Reparatur der fehlenden Komponenten."
            )
            self.btn_start.setAccessibleName("Starten")
            self.btn_start.setAccessibleDescription(
                "Startet das Hauptprogramm nach erfolgreicher Prüfung."
            )
            self.btn_exit.setAccessibleName("Beenden")
            self.btn_exit.setAccessibleDescription(
                "Schließt den Launcher ohne Änderungen."
            )

            self.btn_fix.clicked.connect(self._fix_all)
            self.btn_start.clicked.connect(self.accept)
            self.btn_exit.clicked.connect(self.reject)

            lay = QtWidgets.QVBoxLayout(self)
            theme_row = QtWidgets.QHBoxLayout()
            theme_row.addWidget(self.theme_label)
            theme_row.addWidget(self.theme_select)
            theme_row.addStretch(1)
            theme_row.addWidget(self.debug_check)
            lay.addLayout(theme_row)
            lay.addWidget(self.info)
            lay.addWidget(self.progress)
            lay.addWidget(self.status_label)
            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.btn_fix)
            row.addWidget(self.btn_start)
            row.addWidget(self.btn_exit)
            lay.addLayout(row)
            QtWidgets.QWidget.setTabOrder(self.theme_select, self.debug_check)
            QtWidgets.QWidget.setTabOrder(self.debug_check, self.info)
            QtWidgets.QWidget.setTabOrder(self.info, self.progress)
            QtWidgets.QWidget.setTabOrder(self.progress, self.btn_fix)
            QtWidgets.QWidget.setTabOrder(self.btn_fix, self.btn_start)
            QtWidgets.QWidget.setTabOrder(self.btn_start, self.btn_exit)

        def _start_check(self):
            self.btn_fix.setEnabled(False)
            self.btn_start.setEnabled(False)
            self.info.setHtml("<p>Prüfung läuft…</p>")
            self._check_worker = CheckWorker()
            self._check_worker.results_ready.connect(self._handle_results)
            self._check_worker.failed.connect(self._handle_error)
            self._check_worker.start()

        def _handle_results(self, results):
            launcher_checks.LOGGER.info("Check results: %s", results)
            html, pct = self._render_results(results)
            self.info.setHtml(html)
            self.progress.setValue(pct)
            self.btn_fix.setEnabled(True)
            self.btn_start.setEnabled(self._all_required_ok(results))

        def _set_busy(self, busy: bool) -> None:
            self.btn_fix.setEnabled(not busy)
            self.btn_start.setEnabled(not busy and self.progress.value() == 100)
            self.btn_exit.setEnabled(not busy)
            self.status_label.setText(
                "Installation laeuft…" if busy else "Bereit."
            )

        def _check(self):
            self.missing_pkgs = [
                p
                for p in launcher_checks.REQ_PKGS
                p for p in launcher_checks.REQ_PKGS
                if not launcher_checks.pip_show(self.py, p)
            ]
            self.ffmpeg_ok = shutil.which("ffmpeg") and shutil.which("ffprobe")

        def _handle_error(self, message):
            self.info.setHtml(f"<p>Fehler bei der Prüfung: {message}</p>")
            self.btn_fix.setEnabled(True)

        def _render_results(self, results):
            pct = 0
            items = []
            tips = []
            required_count = len([r for r in results if r.blocking])
            required_count = max(required_count, 1)
            for result in results:
                icon = "✅" if result.ok else "❌"
                color = "#1b7f2a" if result.ok else "#a11a1a"
                items.append(
                    f"<li><span style='color:{color};'>{icon} "
                    f"{result.title}:</span> {result.detail}</li>"
                )
                if result.ok and result.blocking:
                    pct += 100 / required_count
                if not result.ok and result.fix_hint:
                    tips.append(f"<li>{result.fix_hint}</li>")

            tips_html = ""
            if tips:
                tips_html = (
                    "<h4>Laien-Tipps (einfache Schritte)</h4>"
                    "<ul>" + "".join(tips) + "</ul>"
                )

            html = (
                "<h3>Status-Checkliste</h3><ul>" + "".join(items) + "</ul>"
                "<p>Mit »Automatisch reparieren« werden die Schritte der Reihe nach "
                "ausgeführt.</p>" + tips_html
            )
            return html, round(pct)

        @staticmethod
        def _all_required_ok(results):
            return all(result.ok for result in results if result.blocking)

        def _fix_all(self):
            self.setEnabled(False)
            self.info.setHtml("<p>Reparatur läuft…</p>")
            self._fix_worker = FixWorker()
            self._fix_worker.results_ready.connect(self._handle_fix_results)
            self._fix_worker.failed.connect(self._handle_fix_error)
            self._fix_worker.start()

        def _handle_fix_results(self, results):
            offline_skips = [r for r in results if r.skipped_offline]
            detail_lines = [
                f"<li>{'✅' if r.ok else '❌'} {r.title}: {r.detail}</li>"
                for r in results
            ]
            offline_note = (
                "<p><strong>Kein Internet, Installation übersprungen.</strong></p>"
                if offline_skips
                else ""
            )
            self.info.setHtml(
                "<h3>Reparatur-Ergebnis</h3><ul>"
                + "".join(detail_lines)
                + "</ul>"
                + offline_note
            )
            self.setEnabled(True)
            self._start_check()

        def _handle_fix_error(self, message):
            QtWidgets.QMessageBox.critical(
                self, "Fehler", f"Reparatur fehlgeschlagen:\n{message}"
            )
            self.setEnabled(True)
            self._start_check()

        def _toggle_debug(self, enabled):
            self._debug_enabled = enabled
            os.environ["VT_DEBUG"] = "1" if enabled else "0"
            setup_logging(enabled)

        def _apply_theme(self, theme_name: str):
            if theme_name == "Dunkel":
                palette = QtGui.QPalette()
                palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#1f1f1f"))
                palette.setColor(
                    QtGui.QPalette.WindowText, QtGui.QColor("#f2f2f2")
                )
                palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#2b2b2b"))
                palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#f2f2f2"))
                palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#333333"))
                palette.setColor(
                    QtGui.QPalette.ButtonText, QtGui.QColor("#f2f2f2")
                )
                self.setPalette(palette)
            elif theme_name == "Hoher Kontrast":
                palette = QtGui.QPalette()
                palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#000000"))
                palette.setColor(
                    QtGui.QPalette.WindowText, QtGui.QColor("#ffffff")
                )
                palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#000000"))
                palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#ffffff"))
                palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#000000"))
                palette.setColor(
                    QtGui.QPalette.ButtonText, QtGui.QColor("#ffffff")
                )
                self.setPalette(palette)
            else:
                self.setPalette(self.style().standardPalette())
            if self.worker and self.worker.isRunning():
                return
            self._set_busy(True)
            self.progress.setValue(0)
            self.status_label.setText("Installation laeuft…")
            self.worker = InstallWorker(self.py, self.missing_pkgs, self.ffmpeg_ok)
            self.worker.progress.connect(self._on_progress)
            self.worker.finished.connect(self._on_fix_finished)
            self.worker.start()

        def _on_progress(self, value: int, text: str) -> None:
            self.progress.setValue(max(0, min(100, value)))
            self.status_label.setText(text)

        def _show_error(
            self,
            title: str,
            message: str,
            details: str,
            permission: bool,
        ) -> None:
            msg = QtWidgets.QMessageBox(self)
            msg.setWindowTitle(title)
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText(message)
            details_btn = None
            if permission:
                details_btn = msg.addButton(
                    "Details anzeigen",
                    QtWidgets.QMessageBox.ActionRole,
                )
                msg.addButton(QtWidgets.QMessageBox.Ok)
            else:
                msg.setDetailedText(details)
                msg.addButton(QtWidgets.QMessageBox.Ok)
            msg.exec()
            if (
                permission
                and details_btn is not None
                and msg.clickedButton() == details_btn
            ):
                QtWidgets.QMessageBox.information(
                    self,
                    "Details",
                    details,
                )

        def _on_fix_finished(self, result: dict) -> None:
            self.missing_pkgs = result.get("missing_pkgs", [])
            self.ffmpeg_ok = result.get("ffmpeg_ok", False)
            for err in result.get("errors", []):
                self._show_error(
                    err.get("title", "Fehler"),
                    err.get("message", "Es ist ein Fehler aufgetreten."),
                    err.get("details", ""),
                    bool(err.get("permission", False)),
                )
            self._set_busy(False)
            self._check()

    return Wizard, QtWidgets, QtCore, QtGui


def main():
    bootstrap_console()

    try:
        Wizard, QtWidgets, _, _ = build_wizard()
    except Exception as e:
        print("Qt konnte nicht geladen werden:", e)
        sys.exit(1)

    setup_logging(os.environ.get("VT_DEBUG") == "1")
    app = QtWidgets.QApplication(sys.argv)
    wiz = Wizard()
    if wiz.exec() != QtWidgets.QDialog.Accepted:
        sys.exit(0)

    try:
        import videobatch_gui as gui
    except Exception as e:
        print("Fehler beim Laden der Oberfl\u00e4che:", e)
        sys.exit(1)

    try:
        w = gui.MainWindow()
        w.show()
        sys.exit(app.exec())
    except Exception as e:
        print("Fehler beim Start des Tools:", e)
        if hasattr(gui, "LOG_FILE"):
            print("Details stehen in", gui.LOG_FILE)
        sys.exit(1)


if __name__ == "__main__":
    main()
