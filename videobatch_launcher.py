# =========================================
# QUICKSTART
# Start (alles automatisch):   python3 videobatch_launcher.py
# Edit mit micro:              micro videobatch_launcher.py
# Venv löschen (Reset):        rm -rf .videotool_env
# =========================================

from __future__ import annotations
import sys
import os
import subprocess
import shutil
from pathlib import Path

REQ_PKGS = ["PySide6", "Pillow", "ffmpeg-python"]
ENV_DIR = Path(".videotool_env").resolve()
SELF = Path(__file__).resolve()
FLAG = "VT_BOOTSTRAPPED"


def in_venv() -> bool:
    return (hasattr(sys, "real_prefix")
            or getattr(sys, "base_prefix", sys.prefix) != sys.prefix
            or os.environ.get("VIRTUAL_ENV"))


def venv_python() -> Path:
    """Return path to launcher venv or current interpreter if missing."""
    path = ENV_DIR / ("Scripts" if os.name == "nt" else "bin") / "python"
    return path if path.exists() else Path(sys.executable)


def ensure_venv() -> None:
    if not ENV_DIR.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(ENV_DIR)])


def pip_show(py: str, pkg: str) -> bool:
    return subprocess.run([py, "-m", "pip", "show", pkg],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0


def pip_install(py: str, pkgs: list[str]) -> None:
    if not pkgs:
        return
    subprocess.check_call(
        [py, "-m", "pip", "install", "--upgrade", "pip"], stdout=subprocess.DEVNULL
    )
    subprocess.check_call([py, "-m", "pip", "install", "--upgrade"] + pkgs)


def reboot_into_venv():
    py_path = Path(venv_python())
    if not py_path.exists():
        try:
            ensure_venv()
        except Exception as e:
            print("Konnte virtuelle Umgebung nicht erstellen:", e)
            py_path = Path(sys.executable)
        else:
            path_obj = ENV_DIR / ("Scripts" if os.name == "nt" else "bin") / "python"
            py_path = Path(venv_python()) if path_obj.exists() else Path(sys.executable)

    env = os.environ.copy()
    env[FLAG] = "1"
    try:
        os.execvpe(str(py_path), [str(py_path), str(SELF)], env)
    except FileNotFoundError:
        print("Python-Interpreter nicht gefunden:", py_path)
        os.execvpe(sys.executable, [sys.executable, str(SELF)], env)


def bootstrap_console():
    if not in_venv():
        ensure_venv()
        reboot_into_venv()
    elif ENV_DIR.exists() and os.environ.get(FLAG) != "1":
        reboot_into_venv()

    py = str(venv_python())
    missing = [p for p in REQ_PKGS if not pip_show(py, p)]
    if missing:
        pip_install(py, missing)


def main():
    bootstrap_console()

    try:
        from PySide6 import QtWidgets
    except Exception as e:
        print("Qt konnte nicht geladen werden:", e)
        sys.exit(1)
    import subprocess as sp

    class Wizard(QtWidgets.QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("VideoBatchTool – Setup")
            self.resize(600, 420)
            self.py = str(venv_python())
            self._build_ui()
            self._check()

        def _build_ui(self):
            self.info = QtWidgets.QTextBrowser()
            self.info.setOpenExternalLinks(True)
            self.progress = QtWidgets.QProgressBar(maximum=100)

            self.btn_fix = QtWidgets.QPushButton("Installieren / Reparieren")
            self.btn_start = QtWidgets.QPushButton("Tool starten →")
            self.btn_exit = QtWidgets.QPushButton("Beenden")

            self.btn_fix.clicked.connect(self._fix_all)
            self.btn_start.clicked.connect(self.accept)
            self.btn_exit.clicked.connect(self.reject)

            lay = QtWidgets.QVBoxLayout(self)
            lay.addWidget(self.info)
            lay.addWidget(self.progress)
            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.btn_fix)
            row.addWidget(self.btn_start)
            row.addWidget(self.btn_exit)
            lay.addLayout(row)

        def _check(self):
            self.missing_pkgs = [p for p in REQ_PKGS if not pip_show(self.py, p)]
            self.ffmpeg_ok = shutil.which("ffmpeg") and shutil.which("ffprobe")

            pct = 0
            if not self.missing_pkgs:
                pkg_txt = "✔️ Alle Python-Pakete vorhanden"
                pct += 50
            else:
                pkg_txt = "❌ Fehlende Pakete: " + ", ".join(self.missing_pkgs)

            if self.ffmpeg_ok:
                ff_txt = "✔️ ffmpeg/ffprobe gefunden"
                pct += 50
            else:
                ff_txt = "❌ ffmpeg/ffprobe fehlen"

            self.progress.setValue(pct)
            html = (
                "<h3>Status</h3><ul>"
                f"<li>{pkg_txt}</li>"
                f"<li>{ff_txt}</li>"
                "</ul>"
                "<p>Mit »Installieren / Reparieren« wird alles automatisch "
                "eingerichtet.</p>"
            )
            self.info.setHtml(html)
            self.btn_start.setEnabled(pct == 100)

        def _fix_all(self):
            self.setEnabled(False)
            QtWidgets.QApplication.processEvents()

            if self.missing_pkgs:
                try:
                    pip_install(self.py, self.missing_pkgs)
                except Exception as e:
                    QtWidgets.QMessageBox.critical(
                        self,
                        "Fehler",
                        f"Pakete konnten nicht installiert werden:\n{e}",
                    )

            if not self.ffmpeg_ok:
                if sys.platform.startswith("linux"):
                    try:
                        sp.check_call(["sudo", "apt", "update"])
                        sp.check_call(["sudo", "apt", "install", "-y", "ffmpeg"])
                    except Exception as e:
                        QtWidgets.QMessageBox.warning(
                            self,
                            "Fehler",
                            (
                                "ffmpeg konnte nicht automatisch installiert "
                                f"werden.\n{e}"
                            ),
                        )
                self.ffmpeg_ok = shutil.which("ffmpeg") and shutil.which("ffprobe")

            self.setEnabled(True)
            self._check()

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
