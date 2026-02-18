# =========================================
# QUICKSTART
# Start (bevorzugt):           python3 -m app --mode gui
# Legacy (deprecated):         python3 videobatch_launcher.py
# Edit mit micro:              micro videobatch_launcher.py
# Venv löschen (Reset):        rm -rf .videotool_env
# =========================================

from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import sys

from core import launcher_checks
from core.launcher_theme import log_theme_selection, resolve_launcher_theme
from core.paths import log_dir, user_data_dir

SELF = Path(__file__).resolve()
PROJECT_ROOT = SELF.parent
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
    py_path = Path(launcher_checks.venv_python(PROJECT_ROOT))
    if not py_path.exists():
        try:
            launcher_checks.ensure_venv(PROJECT_ROOT)
        except Exception as e:
            print("Konnte virtuelle Umgebung nicht erstellen:", e)
            py_path = Path(sys.executable)
        else:
            path_obj = (
                launcher_checks.env_dir(PROJECT_ROOT)
                / ("Scripts" if os.name == "nt" else "bin")
                / "python"
            )
            py_path = (
                Path(launcher_checks.venv_python(PROJECT_ROOT))
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
        launcher_checks.ensure_venv(PROJECT_ROOT)
        reboot_into_venv()
    elif (
        launcher_checks.env_dir(PROJECT_ROOT).exists()
        and os.environ.get(FLAG) != "1"
    ):
        reboot_into_venv()

    py = str(launcher_checks.venv_python(PROJECT_ROOT))
    missing_pkgs = [
        pkg
        for pkg in launcher_checks.REQ_PKGS
        if not launcher_checks.pip_show(py, pkg)
    ]
    if missing_pkgs:
        try:
            launcher_checks.pip_install(py, missing_pkgs)
        except Exception as exc:
            print(
                "Fehler bei der automatischen Paket-Installation.",
                "Hinweis: Bitte Internetverbindung und Schreibrechte prüfen.",
                f"Details im Log: {LOG_FILE}",
            )
            raise exc


def build_wizard():
    from PySide6 import QtCore, QtGui, QtWidgets

    class CheckWorker(QtCore.QThread):
        results_ready = QtCore.Signal(list)
        failed = QtCore.Signal(str)

        def run(self):
            try:
                results = launcher_checks.collect_checks(
                    str(launcher_checks.venv_python(PROJECT_ROOT)),
                    PROJECT_ROOT,
                    PROJECT_ROOT,
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
                    str(launcher_checks.venv_python(PROJECT_ROOT)),
                    PROJECT_ROOT,
                    PROJECT_ROOT,
                )
            except Exception as exc:
                self.failed.emit(str(exc))
            else:
                self.results_ready.emit(results)

    class Wizard(QtWidgets.QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("VideoBatchTool – Setup")
            self.resize(700, 520)
            self._debug_enabled = os.environ.get("VT_DEBUG") == "1"
            self.resize(600, 420)
            self.py = str(launcher_checks.venv_python(PROJECT_ROOT))
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
                "Wählen Sie das Farbschema für den Launcher. Für sehschwache Personen ist Hoher Kontrast empfohlen."
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
            self.info.setHtml(
                "<p>Prüfung läuft…</p>"
                "<p><strong>Tipp für gute Lesbarkeit:</strong> Nutzen Sie bei Bedarf "
                "<em>Hoher Kontrast</em> und aktivieren Sie <em>Debug-Log</em> "
                "für klare Fehlermeldungen in einfacher Sprache.</p>"
            )
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
                if not launcher_checks.pip_show(self.py, p)
            ]
            self.ffmpeg_ok = shutil.which("ffmpeg") and shutil.which("ffprobe")

        def _handle_error(self, message):
            self.info.setHtml(f"<p>Fehler bei der Prüfung: {message}</p>")
            self.btn_fix.setEnabled(True)

        def _render_results(self, results):
            pct = 0.0
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

            feedback = launcher_checks.build_check_feedback(results)
            steps_html = "".join(
                f"<li>{step}</li>" for step in feedback["next_steps"]
            )
            terms_html = "".join(
                f"<li>{term}</li>" for term in feedback["beginner_terms"]
            )
            commands = feedback["quick_commands"]
            commands_html = "".join(
                f"<li><code>{cmd}</code></li>" for cmd in commands
            )
            command_section = (
                "<h4>Schnelle Befehle (Terminal)</h4><ul>"
                + commands_html
                + "</ul><p>Diese Befehle koennen 1:1 kopiert werden.</p>"
                if commands
                else ""
            )
            html = (
                f"<h3>{feedback['headline']}</h3>"
                f"<p><strong>{feedback['summary']}</strong></p>"
                "<h4>Status-Checkliste</h4><ul>" + "".join(items) + "</ul>"
                "<h4>Naechste Schritte</h4><ul>" + steps_html + "</ul>"
                "<h4>Begriffe einfach erklaert</h4><ul>"
                + terms_html
                + "</ul>"
                + command_section
                + "<p>Mit »Automatisch reparieren« werden die Schritte der Reihe "
                "nach ausgefuehrt.</p>" + tips_html
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
            feedback = launcher_checks.build_repair_feedback(results)
            offline_note = (
                "<p><strong>Kein Internet, Installation übersprungen.</strong></p>"
                if offline_skips
                else ""
            )
            hints_html = ""
            if feedback["hints"]:
                hints_html = (
                    "<h4>Naechste Schritte (einfach erklaert)</h4><ul>"
                    + "".join(f"<li>{hint}</li>" for hint in feedback["hints"])
                    + "</ul>"
                )
            self.info.setHtml(
                f"<h3>{feedback['headline']}</h3>"
                f"<p><strong>{feedback['summary']}</strong></p>"
                "<h4>Reparatur-Ergebnis</h4><ul>"
                + "".join(detail_lines)
                + "</ul>"
                + offline_note
                + hints_html
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
            launcher_checks.LOGGER.info(
                "Debug-Modus %s. Hinweise sind in %s gespeichert.",
                "aktiv" if enabled else "inaktiv",
                LOG_FILE,
            )

        def _apply_theme(self, theme_name: str):
            try:
                resolved_theme = log_theme_selection(
                    theme_name,
                    launcher_checks.LOGGER,
                )
                palette_values = resolve_launcher_theme(resolved_theme)
            except (TypeError, ValueError) as exc:
                launcher_checks.LOGGER.warning(
                    "Ungueltiger Theme-Wechsel: %s", exc
                )
                self.setPalette(self.style().standardPalette())
                return

            palette = QtGui.QPalette()
            palette.setColor(
                QtGui.QPalette.ColorRole.Window,
                QtGui.QColor(palette_values["window"]),
            )
            palette.setColor(
                QtGui.QPalette.ColorRole.WindowText,
                QtGui.QColor(palette_values["window_text"]),
            )
            palette.setColor(
                QtGui.QPalette.ColorRole.Base,
                QtGui.QColor(palette_values["base"]),
            )
            palette.setColor(
                QtGui.QPalette.ColorRole.Text,
                QtGui.QColor(palette_values["text"]),
            )
            palette.setColor(
                QtGui.QPalette.ColorRole.Button,
                QtGui.QColor(palette_values["button"]),
            )
            palette.setColor(
                QtGui.QPalette.ColorRole.ButtonText,
                QtGui.QColor(palette_values["button_text"]),
            )
            self.setPalette(palette)

    return Wizard, QtWidgets, QtCore, QtGui


def main() -> int:
    print(
        "⚠️  videobatch_launcher.py ist deprecated. "
        "Bitte nutzen: python3 -m app --mode gui"
    )
    from app import main as primary_main

    forwarded_args = ["--mode", "gui"]
    if os.environ.get("VT_DEBUG") == "1":
        forwarded_args.append("--debug")
    return int(primary_main(forwarded_args))


if __name__ == "__main__":
    raise SystemExit(main())
