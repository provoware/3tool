# =========================================
# QUICKSTART
# Direktstart (wenn alles installiert):  python3 videobatch_gui.py
# Empfohlen (Auto-Setup):                python3 start_gui.py
# Edit mit micro:                        micro videobatch_gui.py
# =========================================

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.parse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PySide6 import QtCore, QtGui, QtMultimedia, QtWidgets
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHeaderView

from core.media_validation import (
    AUDIO_EXTENSIONS,
    IMAGE_EXTENSIONS,
)
from core.fallback_media import (
    dumps_audio_list,
    loads_audio_list,
    persist_fallback_media,
)
from core.output_management import (
    build_dated_output_dir,
    transfer_with_validation,
)
from core.paths import config_dir, log_dir, user_data_dir
from core.plugins import PluginManager
from core.themes import get_theme_tokens, load_themes
from core.ui_profiles import resolve_interface_profile, resolve_spacing_profile
from core.ui_texts import load_ui_texts, text_with_fallback
from core.utils import build_out_name, probe_duration
from core.validation import normalize_audio_bitrate, validate_output_template
from gui.dialogs.file_picker import FilePickerDialog
from gui.main_window import build_initial_state
from gui.views.main_window_view import create_action_buttons
from gui.services.preview import play_audio_preview, stop_audio_preview
from gui.services.runtime_paths import (
    build_default_runtime_paths,
    check_ffmpeg,
    safe_move,
)
from gui.services.project_io import (
    build_project_payload,
    load_project_file,
    make_project_relative,
    resolve_project_path,
    save_project_file,
)
from gui.state.project_state import (
    get_project_root,
    get_project_start_dir,
    set_last_project_path,
    set_project_root,
)
from gui.views.action_orchestration import choose_project_root_dialog
from gui.widgets.dashboard import InfoDashboard

# ---------- Paths ----------
APP_DIR = user_data_dir()
CONFIG_DIR = config_dir()
LOG_DIR = log_dir()
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = CONFIG_DIR / "settings.ini"

# ---------- Logging ----------
LOG_FILE = LOG_DIR / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("VideoBatchTool")

THEMES = load_themes(logger)
UI_TEXTS = load_ui_texts(logger)

# ---------- Helpers ----------
SLIDESHOW_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
OUTPUT_EXTENSIONS = (".mp4", ".mkv", ".avi", ".mov")
MAX_PREVIEW_CACHE_ITEMS = 180
_RUNTIME_PATHS = build_default_runtime_paths()


def get_used_dir() -> Path:
    return _RUNTIME_PATHS.used_dir


def default_output_dir() -> Path:
    return _RUNTIME_PATHS.output_dir


def default_project_dir() -> Path:
    return _RUNTIME_PATHS.project_dir


def default_downloads_dir() -> Path:
    return _RUNTIME_PATHS.downloads_dir


# ---------- Datenmodell ----------
from gui.views.pair_table import PairItem, PairTableModel


# ---------- Worker ----------
class EncodeWorker(QtCore.QObject):
    row_progress = Signal(int, float)
    overall_progress = Signal(float)
    row_error = Signal(int, str)
    log = Signal(str)
    finished = Signal()

    def __init__(
        self,
        pairs: List[PairItem],
        settings: Dict[str, Any],
        copy_only: bool,
        plugin_manager: Optional[PluginManager] = None,
    ):
        super().__init__()
        self.pairs = pairs
        self.settings = settings
        self.copy_only = copy_only
        self._stop_event = threading.Event()
        self._process_lock = threading.Lock()
        self._processes: List[subprocess.Popen] = []
        self._progress_lock = threading.Lock()
        self._completed = 0
        self.plugin_manager = plugin_manager

    def stop(self):
        self._stop_event.set()
        with self._process_lock:
            for proc in list(self._processes):
                try:
                    proc.kill()
                except (OSError, ProcessLookupError, PermissionError) as exc:
                    logger.debug(
                        "encode.stop.kill_failed",
                        extra={
                            "pid": getattr(proc, "pid", None),
                            "error": str(exc),
                        },
                    )
                    continue

    def _escape_ffmpeg_path(self, path: Path) -> str:
        return path.as_posix().replace("'", r"\'")

    def _register_process(self, proc: subprocess.Popen) -> None:
        with self._process_lock:
            self._processes.append(proc)

    def _unregister_process(self, proc: subprocess.Popen) -> None:
        with self._process_lock:
            if proc in self._processes:
                self._processes.remove(proc)

    def _mark_complete(self, total: int) -> None:
        with self._progress_lock:
            self._completed += 1
            completed = self._completed
        self.overall_progress.emit(completed / max(1, total) * 100.0)

    def _encode_item(self, index: int, item: PairItem, total: int) -> None:
        list_path: Optional[str] = None
        if self._stop_event.is_set():
            item.status = "ABGEBROCHEN"
            self._mark_complete(total)
            return
        item.validate()
        if not item.valid:
            item.status = "FEHLER"
            self.row_error.emit(index, item.validation_msg)
            self._mark_complete(total)
            return
        proc: Optional[subprocess.Popen] = None
        try:
            item.status = "ENCODIERE"
            item.progress = 0.0
            self.row_progress.emit(index, 0.0)
            out_dir = build_dated_output_dir(
                Path(self.settings["out_dir"]),
                self.settings.get("mode", "Standard"),
            )
            self.log.emit(f"Ausgabeordner gesetzt: {out_dir}")
            w, h = self.settings["width"], self.settings["height"]
            crf = self.settings["crf"]
            preset = self.settings["preset"]
            ab = self.settings["abitrate"]
            duration = item.duration or 1
            mode = self.settings.get("mode", "Standard")
            quality_label = f"crf{crf}_{preset}"
            form_label = mode.replace(" + ", "_").replace(" ", "_")
            item.output = build_out_name(
                item.audio_path,
                out_dir,
                self.settings.get("output_template"),
                duration_seconds=item.duration,
                quality=quality_label,
                resolution=f"{w}x{h}",
                form=form_label,
            )
            if mode == "Video + Audio":
                vdur = probe_duration(item.image_path)
                extra = max(0.0, duration - vdur)
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    item.image_path,
                    "-i",
                    item.audio_path,
                ]
                if extra > 0:
                    cmd += [
                        "-vf",
                        f"tpad=stop_mode=clone:stop_duration={extra}",
                        "-c:v",
                        "libx264",
                    ]
                else:
                    cmd += ["-c:v", "copy"]
                cmd += [
                    "-c:a",
                    "aac",
                    "-b:a",
                    ab,
                    "-shortest",
                    "-preset",
                    preset,
                    "-crf",
                    str(crf),
                    item.output,
                ]
            elif mode == "Slideshow":
                img_dir = Path(item.image_path)
                imgs = []
                for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp"):
                    imgs.extend(sorted(img_dir.glob(ext)))
                if not imgs:
                    raise Exception("Keine Bilder für Slideshow")
                per = duration / len(imgs) if duration else 2
                with tempfile.NamedTemporaryFile(
                    delete=False, mode="w", suffix=".txt"
                ) as f:
                    for im in imgs:
                        escaped_path = self._escape_ffmpeg_path(im)
                        f.write(f"file '{escaped_path}'\n")
                        f.write(f"duration {per}\n")
                    escaped_last = self._escape_ffmpeg_path(imgs[-1])
                    f.write(f"file '{escaped_last}'\n")
                    list_path = f.name
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    list_path,
                    "-i",
                    item.audio_path,
                    "-c:v",
                    "libx264",
                    "-vf",
                    f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
                    "-c:a",
                    "aac",
                    "-b:a",
                    ab,
                    "-shortest",
                    "-preset",
                    preset,
                    "-crf",
                    str(crf),
                    item.output,
                ]
            else:
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-loop",
                    "1",
                    "-i",
                    item.image_path,
                    "-i",
                    item.audio_path,
                    "-c:v",
                    "libx264",
                    "-tune",
                    "stillimage",
                    "-vf",
                    f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
                    "-c:a",
                    "aac",
                    "-b:a",
                    ab,
                    "-shortest",
                    "-preset",
                    preset,
                    "-crf",
                    str(crf),
                    item.output,
                ]
            if self.plugin_manager is not None:
                payload = self.plugin_manager.run_hook(
                    "before_encode",
                    {
                        "command": cmd,
                        "mode": mode,
                        "image": item.image_path,
                        "audio": item.audio_path,
                        "output": str(item.output),
                    },
                )
                cmd = payload.get("command", cmd)
            proc = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
            )
            self._register_process(proc)
            if proc.stderr:
                for line in proc.stderr:
                    if self._stop_event.is_set():
                        proc.kill()
                        break
                    if "time=" in line and duration:
                        try:
                            t = line.split("time=")[1].split(" ")[0]
                            h_, m_, s_ = t.split(":")
                            elapsed = (
                                float(h_) * 3600 + float(m_) * 60 + float(s_)
                            )
                            perc = min(100.0, elapsed / duration * 100.0)
                            item.progress = perc
                            self.row_progress.emit(index, perc)
                        except (ValueError, AttributeError) as exc:
                            logger.warning(
                                "encode.progress_parse_failed",
                                extra={"line": line.strip(), "error": str(exc)},
                            )
            proc.wait()
            if self._stop_event.is_set():
                item.status = "ABGEBROCHEN"
                self.log.emit("Abbruch durch Benutzer.")
            elif proc.returncode != 0:
                item.status = "FEHLER"
                self.row_error.emit(index, "FFmpeg-Fehler")
                self.log.emit(f"FFmpeg-Fehler bei {item.output}")
            else:
                item.status = "FERTIG"
                item.progress = 100.0
                self.row_progress.emit(index, 100.0)
                self.log.emit(f"Fertig: {item.output}")
                if self.plugin_manager is not None:
                    self.plugin_manager.run_hook(
                        "after_encode",
                        {"output": str(item.output), "mode": mode},
                    )
        except (
            FileNotFoundError,
            PermissionError,
            OSError,
            ValueError,
            subprocess.SubprocessError,
        ) as exc:
            item.status = "FEHLER"
            user_msg = (
                "Der Vorgang konnte nicht fertiggestellt werden. "
                "Ursache: Datei fehlt, keine Rechte oder Tool-Fehler. "
                "Nächster Schritt: Eingaben prüfen und Test starten mit "
                "'python3 videobatch_extra.py --selftest'."
            )
            self.row_error.emit(index, user_msg)
            file_hint = (
                item.output
                or item.image_path
                or item.audio_path
                or "unbekannte Datei"
            )
            logger.exception(
                "encode.row_failed",
                extra={
                    "index": index,
                    "file_hint": str(file_hint),
                    "error": str(exc),
                },
            )
            self.log.emit(f"Fehler bei {file_hint}: {user_msg} (Detail: {exc})")
        finally:
            if list_path:
                try:
                    Path(list_path).unlink(missing_ok=True)
                except (
                    FileNotFoundError,
                    PermissionError,
                    OSError,
                ) as cleanup_error:
                    logger.warning(
                        "encode.cleanup_list_failed",
                        extra={
                            "list_path": list_path,
                            "error": str(cleanup_error),
                        },
                    )
                    self.log.emit(
                        "Temporäre Liste konnte nicht gelöscht werden. "
                        "Nächster Schritt: Datei manuell entfernen mit "
                        f"'rm -f {list_path}'. Detail: {cleanup_error}"
                    )
            if proc is not None:
                self._unregister_process(proc)
            self._mark_complete(total)

    def run(self):
        total = len(self.pairs)
        parallel_jobs = max(1, int(self.settings.get("parallel_jobs", 1)))
        if parallel_jobs == 1:
            for i, item in enumerate(self.pairs):
                self._encode_item(i, item, total)
                if self._stop_event.is_set():
                    break
        else:
            with ThreadPoolExecutor(max_workers=parallel_jobs) as executor:
                futures = [
                    executor.submit(self._encode_item, i, item, total)
                    for i, item in enumerate(self.pairs)
                ]
                while futures:
                    _, futures = wait(futures, return_when=FIRST_COMPLETED)
                    if self._stop_event.is_set():
                        for future in futures:
                            future.cancel()
                        break
        if all(p.status == "FERTIG" for p in self.pairs):
            try:
                used_root = get_used_dir() / datetime.now().strftime("%Y-%m-%d")
                tracks_dir = used_root / "tracks"
                musik_dir = used_root / "musik"
                moved = 0
                for p in self.pairs:
                    for f in (p.image_path, p.audio_path):
                        if not f or not Path(f).exists():
                            continue
                        src_path = Path(f)
                        target_dir = (
                            musik_dir
                            if src_path.suffix.lower() in AUDIO_EXTENSIONS
                            else tracks_dir
                        )
                        result = transfer_with_validation(
                            src_path,
                            target_dir,
                            copy_only=self.copy_only,
                            suffix_label="benutzt",
                        )
                        if result.validated:
                            moved += 1
                        self.log.emit(
                            f"Eingabe-Datei {result.action}: {result.target} | {result.detail}"
                        )
                self.log.emit(
                    f"{moved} Dateien nach {used_root} "
                    f"{'kopiert' if self.copy_only else 'verschoben'} und validiert."
                )
            except (
                FileNotFoundError,
                PermissionError,
                OSError,
                shutil.Error,
            ) as exc:
                logger.exception(
                    "encode.archive_failed", extra={"error": str(exc)}
                )
                self.log.emit(
                    "Archivierung fehlgeschlagen. Ursache: Datei fehlt oder Rechteproblem. "
                    "Nächster Schritt: Zielordner prüfen und erneut starten. "
                    "Befehl: python3 start_gui.py --debug "
                    f"(Detail: {exc})"
                )
        self.finished.emit()


# ---------- UI Widgets ----------
class DropListWidget(QtWidgets.QListWidget):
    files_dropped = Signal(list)

    def __init__(self, title: str, patterns: Tuple[str, ...]):
        super().__init__()
        self.patterns = patterns
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setToolTip(title)
        self.setStatusTip(title)
        self.itemDoubleClicked.connect(self._open_item)

    def _notify_structure_update(self) -> None:
        wnd = self.window()
        if hasattr(wnd, "_refresh_structure_view"):
            wnd._refresh_structure_view()

    def _sort_value(self, path: str, mode: str):
        file_path = Path(path)
        if mode == "name":
            return file_path.name.lower()
        if mode == "path":
            return str(file_path).lower()
        if mode == "mtime":
            try:
                return file_path.stat().st_mtime
            except FileNotFoundError:
                return 0
        if mode == "size":
            try:
                return file_path.stat().st_size
            except FileNotFoundError:
                return 0
        return str(file_path).lower()

    def _sort_items(self, mode: str, reverse: bool = False) -> None:
        items = [self.item(i) for i in range(self.count())]
        items.sort(
            key=lambda item: self._sort_value(
                item.data(Qt.UserRole) or "", mode
            ),
            reverse=reverse,
        )
        self.clear()
        for item in items:
            self.addItem(item)

    def _add_sort_menu(
        self, menu: QtWidgets.QMenu
    ) -> Dict[QAction, Tuple[str, bool]]:
        sort_menu = menu.addMenu("Sortieren")
        actions: Dict[QAction, Tuple[str, bool]] = {}
        actions[sort_menu.addAction("Name A → Z")] = ("name", False)
        actions[sort_menu.addAction("Name Z → A")] = ("name", True)
        actions[sort_menu.addAction("Datum neu → alt")] = ("mtime", True)
        actions[sort_menu.addAction("Datum alt → neu")] = ("mtime", False)
        actions[sort_menu.addAction("Größe groß → klein")] = ("size", True)
        actions[sort_menu.addAction("Größe klein → groß")] = ("size", False)
        actions[sort_menu.addAction("Pfad A → Z")] = ("path", False)
        return actions

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragMoveEvent(e)

    def dropEvent(self, e):
        files = [u.toLocalFile() for u in e.mimeData().urls()]
        acc = [
            f
            for f in files
            if Path(f).is_dir() or f.lower().endswith(self.patterns)
        ]
        if acc:
            self.add_files(acc)
            self.files_dropped.emit(acc)
        e.acceptProposedAction()

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return
        mime = QtCore.QMimeData()
        mime.setUrls([QtCore.QUrl.fromLocalFile(item.data(Qt.UserRole))])
        drag = QtGui.QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)

    def add_files(self, files: List[str]):
        for f in files:
            it = QtWidgets.QListWidgetItem(Path(f).name)
            it.setData(Qt.UserRole, f)
            self.addItem(it)

    def selected_paths(self) -> List[str]:
        return [i.data(Qt.UserRole) for i in self.selectedItems()]

    def contextMenuEvent(self, e: QtGui.QContextMenuEvent):
        item = self.itemAt(e.pos())
        if not item:
            return
        path = item.data(Qt.UserRole)
        menu = QtWidgets.QMenu(self)
        act_open = menu.addAction("Im Ordner zeigen")
        act_copy = menu.addAction("Pfad kopieren")
        act_remove = menu.addAction("Entfernen")
        sort_actions = self._add_sort_menu(menu)
        act = menu.exec(e.globalPos())
        if act == act_open:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))
            self.window()._log(f"Im Ordner gezeigt: {path}")
        elif act == act_copy:
            QtWidgets.QApplication.clipboard().setText(str(path))
            self.window()._log(f"Pfad kopiert: {path}")
        elif act == act_remove:
            self.takeItem(self.row(item))
            self.window()._log(f"Eintrag entfernt: {path}")
            self._notify_structure_update()
        elif act in sort_actions:
            mode, reverse = sort_actions[act]
            self._sort_items(mode, reverse=reverse)
            wnd = self.window()
            if hasattr(wnd, "_log"):
                wnd._log("Liste sortiert")
        e.accept()

    def _open_item(self, item: QtWidgets.QListWidgetItem):
        path = item.data(Qt.UserRole)
        if path:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))
            wnd = self.window()
            if hasattr(wnd, "_log"):
                wnd._log(f"Im Ordner gezeigt: {path}")


class ImageListWidget(DropListWidget):
    add_to_fav = Signal(str)

    def contextMenuEvent(self, e: QtGui.QContextMenuEvent):
        item = self.itemAt(e.pos())
        if not item:
            return
        path = item.data(Qt.UserRole)
        menu = QtWidgets.QMenu(self)
        act_open = menu.addAction("Im Ordner zeigen")
        act_copy = menu.addAction("Pfad kopieren")
        act_fav = menu.addAction("Zu Favoriten")
        act_remove = menu.addAction("Entfernen")
        sort_actions = self._add_sort_menu(menu)
        act = menu.exec(e.globalPos())
        if act == act_open:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))
            self.window()._log(f"Im Ordner gezeigt: {path}")
        elif act == act_copy:
            QtWidgets.QApplication.clipboard().setText(str(path))
            self.window()._log(f"Pfad kopiert: {path}")
        elif act == act_remove:
            self.takeItem(self.row(item))
            self.window()._log(f"Eintrag entfernt: {path}")
            self._notify_structure_update()
        elif act == act_fav:
            self.add_to_fav.emit(path)
            self.window()._log(f"Zu Favoriten: {path}")
        elif act in sort_actions:
            mode, reverse = sort_actions[act]
            self._sort_items(mode, reverse=reverse)
            self.window()._log("Liste sortiert")
        e.accept()


class AudioListWidget(DropListWidget):
    def contextMenuEvent(self, e: QtGui.QContextMenuEvent):
        item = self.itemAt(e.pos())
        if not item:
            return
        path = item.data(Qt.UserRole)
        menu = QtWidgets.QMenu(self)
        act_preview = menu.addAction("Vorschau abspielen")
        act_stop = menu.addAction("Vorschau stoppen")
        act_open = menu.addAction("Im Ordner zeigen")
        act_copy = menu.addAction("Pfad kopieren")
        act_remove = menu.addAction("Entfernen")
        sort_actions = self._add_sort_menu(menu)
        act = menu.exec(e.globalPos())
        wnd = self.window()
        if act == act_preview and hasattr(wnd, "_play_audio_preview"):
            wnd._play_audio_preview(path)
        elif act == act_stop and hasattr(wnd, "_stop_audio_preview"):
            wnd._stop_audio_preview()
        elif act == act_open:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))
            wnd._log(f"Im Ordner gezeigt: {path}")
        elif act == act_copy:
            QtWidgets.QApplication.clipboard().setText(str(path))
            wnd._log(f"Pfad kopiert: {path}")
        elif act == act_remove:
            self.takeItem(self.row(item))
            wnd._log(f"Eintrag entfernt: {path}")
            self._notify_structure_update()
        elif act in sort_actions:
            mode, reverse = sort_actions[act]
            self._sort_items(mode, reverse=reverse)
            wnd._log("Liste sortiert")
        e.accept()

    def _open_item(self, item: QtWidgets.QListWidgetItem):
        path = item.data(Qt.UserRole)
        wnd = self.window()
        if path and hasattr(wnd, "_play_audio_preview"):
            wnd._play_audio_preview(path)
        else:
            super()._open_item(item)


class FavoriteListWidget(DropListWidget):
    use_fav = Signal(str)
    removed = Signal(str)

    def contextMenuEvent(self, e: QtGui.QContextMenuEvent):
        item = self.itemAt(e.pos())
        if not item:
            return
        path = item.data(Qt.UserRole)
        menu = QtWidgets.QMenu(self)
        act_open = menu.addAction("Im Ordner zeigen")
        act_copy = menu.addAction("Pfad kopieren")
        act_use = menu.addAction("Zum Arbeitsbereich")
        act_remove = menu.addAction("Entfernen")
        sort_actions = self._add_sort_menu(menu)
        act = menu.exec(e.globalPos())
        if act == act_open:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))
            self.window()._log(f"Im Ordner gezeigt: {path}")
        elif act == act_copy:
            QtWidgets.QApplication.clipboard().setText(str(path))
            self.window()._log(f"Pfad kopiert: {path}")
        elif act == act_use:
            self.use_fav.emit(path)
            self.window()._log(f"Favorit genutzt: {path}")
        elif act == act_remove:
            self.removed.emit(path)
            self.takeItem(self.row(item))
            self.window()._log(f"Favorit entfernt: {path}")
        elif act in sort_actions:
            mode, reverse = sort_actions[act]
            self._sort_items(mode, reverse=reverse)
            self.window()._log("Liste sortiert")
        e.accept()


class HelpPane(QtWidgets.QTextBrowser):
    def __init__(self, theme_tokens: Optional[Dict[str, str]] = None):
        super().__init__()
        self._theme_tokens: Dict[str, str] = dict(
            theme_tokens or get_theme_tokens("Modern")
        )
        self.setOpenExternalLinks(True)
        self.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHtml(self._html())

    def set_theme_tokens(self, theme_tokens: Dict[str, str]) -> None:
        if not isinstance(theme_tokens, dict):
            logger.warning(
                "Ungueltige Theme-Tokens fuer Hilfe-Bereich ignoriert."
            )
            return
        self._theme_tokens = dict(theme_tokens)
        self.setHtml(self._html())

    def _guide_svg_data(self) -> str:
        fallback_tokens = get_theme_tokens("Modern")
        info_bg = self._theme_tokens.get(
            "preview_info_bg", fallback_tokens["preview_info_bg"]
        )
        info_border = self._theme_tokens.get(
            "preview_info_border", fallback_tokens["preview_info_border"]
        )
        info_fg = self._theme_tokens.get(
            "preview_info_fg", fallback_tokens["preview_info_fg"]
        )
        success_bg = self._theme_tokens.get(
            "preview_success_bg", fallback_tokens["preview_success_bg"]
        )
        success_border = self._theme_tokens.get(
            "preview_success_border",
            fallback_tokens["preview_success_border"],
        )
        success_fg = self._theme_tokens.get(
            "preview_success_fg", fallback_tokens["preview_success_fg"]
        )
        danger_bg = self._theme_tokens.get(
            "preview_danger_bg", fallback_tokens["preview_danger_bg"]
        )
        danger_border = self._theme_tokens.get(
            "preview_danger_border", fallback_tokens["preview_danger_border"]
        )
        danger_fg = self._theme_tokens.get(
            "preview_danger_fg", fallback_tokens["preview_danger_fg"]
        )
        svg = """
        <svg xmlns="http://www.w3.org/2000/svg" width="520" height="120">
          <rect x="10" y="10" width="160" height="100" rx="10" fill="{info_bg}" stroke="{info_border}" stroke-width="2"/>
          <rect x="180" y="10" width="160" height="100" rx="10" fill="{success_bg}" stroke="{success_border}" stroke-width="2"/>
          <rect x="350" y="10" width="160" height="100" rx="10" fill="{danger_bg}" stroke="{danger_border}" stroke-width="2"/>
          <text x="90" y="55" font-size="14" text-anchor="middle" fill="{info_fg}">1. Bilder wählen</text>
          <text x="260" y="55" font-size="14" text-anchor="middle" fill="{success_fg}">2. Audios wählen</text>
          <text x="430" y="55" font-size="14" text-anchor="middle" fill="{danger_fg}">3. Start</text>
          <text x="90" y="80" font-size="11" text-anchor="middle" fill="{info_fg}">Fotos/Ordner</text>
          <text x="260" y="80" font-size="11" text-anchor="middle" fill="{success_fg}">MP3/WAV etc.</text>
          <text x="430" y="80" font-size="11" text-anchor="middle" fill="{danger_fg}">Videos erzeugen</text>
        </svg>
        """.strip().format(
            info_bg=info_bg,
            info_border=info_border,
            info_fg=info_fg,
            success_bg=success_bg,
            success_border=success_border,
            success_fg=success_fg,
            danger_bg=danger_bg,
            danger_border=danger_border,
            danger_fg=danger_fg,
        )
        encoded = urllib.parse.quote(svg)
        return f"data:image/svg+xml;utf8,{encoded}"

    def _html(self) -> str:
        return (
            "<h2>Bedienhilfe</h2>"
            "<ol>"
            "<li>Bilder oder Ordner sowie Audios hineinziehen</li>"
            "<li>Gewünschten Modus wählen (Standard, Slideshow (Diashow), Video + Audio, Mehrere Audios)</li>"
            "<li>Mit 'Auto-Paaren' Dateien koppeln oder selbst zuweisen</li>"
            "<li>Einstellungen prüfen und START klicken</li>"
            "</ol>"
            "<h3>Kurze Beispiele</h3>"
            "<ul>"
            "<li>10 Bilder + 1 MP3 → 1 Video</li>"
            "<li>30 Bilder + 3 MP3 → 3 Videos (je Audio ein Video)</li>"
            "<li>1 Bild + 1 WAV → 1 Video mit Standbild</li>"
            "</ul>"
            "<ul>"
            "<li>Doppelklick editiert Pfade, Rechtsklick öffnet Menü</li>"
            "<li>Kontextmenü kann Pfad kopieren oder Zeile löschen</li>"
            "<li>Rechtsklick auf die Listen öffnet ein Menü zum Entfernen</li>"
            "<li>Hilfe-Menü zeigt README und Logdatei</li>"
            "<li>Knopf 'Öffnen' zeigt den Ausgabeordner</li>"
            "<li>Tooltips zeigen volle Pfade</li>"
            "<li>Menü 'Optionen' hat einen Debug-Schalter (Fehlersuche-Modus) für mehr Meldungen</li>"
            "<li>Preset (Geschwindigkeits-Voreinstellung) passt die Abspielgeschwindigkeit an</li>"
            "<li>Mehr Beispiele im Abschnitt 'Weiterführende Befehle' der Anleitung</li>"
            "<li>Ausführliche Anleitungen: <a href='README.md'>README öffnen</a></li>"
            "<li>Unter 'Ansicht' kann der Log-Bereich ein- oder ausgeblendet werden</li>"
            "<li>Der Log-Pfad steht im Protokollbereich unten</li>"
            "</ul>"
            "<h3>Geführter Start (mit Bild)</h3>"
            "<p>Schritt für Schritt: Bilder wählen → Audios wählen → Start.</p>"
            f"<img src='{self._guide_svg_data()}' alt='Schrittbild: Bilder, Audios, Start' />"
        )


class GuidedWizard(QtWidgets.QDialog):
    def __init__(self, main_window: "MainWindow"):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Geführter Start – Schritt für Schritt")
        self.resize(520, 340)
        self._build_ui()

    def _build_ui(self):
        self.stack = QtWidgets.QStackedWidget()
        self.stack.addWidget(self._page_images())
        self.stack.addWidget(self._page_audios())
        self.stack.addWidget(self._page_start())

        self.btn_back = QtWidgets.QPushButton("Zurück")
        self.btn_next = QtWidgets.QPushButton("Weiter")
        self.btn_close = QtWidgets.QPushButton("Schließen")
        self.btn_back.clicked.connect(self._back)
        self.btn_next.clicked.connect(self._next)
        self.btn_close.clicked.connect(self.reject)

        nav = QtWidgets.QHBoxLayout()
        nav.addWidget(self.btn_back)
        nav.addWidget(self.btn_next)
        nav.addStretch(1)
        nav.addWidget(self.btn_close)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.stack)
        layout.addLayout(nav)
        self._update_buttons()

    def _page_images(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        title = QtWidgets.QLabel("<h3>1. Bilder auswählen</h3>")
        hint = QtWidgets.QLabel(
            "Wähle Bilder oder einen Ordner mit Bildern. "
            "Damit entsteht das Videobild."
        )
        hint.setWordWrap(True)
        btn = QtWidgets.QPushButton("Bilder wählen")
        btn.clicked.connect(self._pick_images)
        lay.addWidget(title)
        lay.addWidget(hint)
        lay.addWidget(btn)
        lay.addStretch(1)
        return w

    def _page_audios(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        title = QtWidgets.QLabel("<h3>2. Audios auswählen</h3>")
        hint = QtWidgets.QLabel(
            "Wähle Audiodateien (z. B. MP3 oder WAV). Audio ist die Tonspur."
        )
        hint.setWordWrap(True)
        btn = QtWidgets.QPushButton("Audios wählen")
        btn.clicked.connect(self._pick_audios)
        lay.addWidget(title)
        lay.addWidget(hint)
        lay.addWidget(btn)
        lay.addStretch(1)
        return w

    def _page_start(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        title = QtWidgets.QLabel("<h3>3. Start</h3>")
        hint = QtWidgets.QLabel(
            "Wenn alles passt, kannst du den Startknopf drücken. "
            "Das Tool erzeugt dann die Videos."
        )
        hint.setWordWrap(True)
        btn = QtWidgets.QPushButton("Start")
        btn.clicked.connect(self._start)
        lay.addWidget(title)
        lay.addWidget(hint)
        lay.addWidget(btn)
        lay.addStretch(1)
        return w

    def _pick_images(self):
        self.main_window._pick_images()
        self._next()

    def _pick_audios(self):
        self.main_window._pick_audios()
        self._next()

    def _start(self):
        self.main_window._start_encode()
        self.accept()

    def _back(self):
        idx = max(0, self.stack.currentIndex() - 1)
        self.stack.setCurrentIndex(idx)
        self._update_buttons()

    def _next(self):
        idx = min(self.stack.count() - 1, self.stack.currentIndex() + 1)
        self.stack.setCurrentIndex(idx)
        self._update_buttons()

    def _update_buttons(self):
        idx = self.stack.currentIndex()
        self.btn_back.setEnabled(idx > 0)
        self.btn_next.setEnabled(idx < self.stack.count() - 1)


# ---------- MainWindow ----------
class MainWindow(QtWidgets.QMainWindow):
    FONT_STEP = 1
    WORKFLOW_SECTION_MIN_WIDTH = 240
    WORKFLOW_SECTION_MIN_HEIGHT = 190

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VideoBatchTool 4.1 – Bild + Audio → MP4")
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        w = min(1200, int(screen.width() * 0.9))
        h = min(800, int(screen.height() * 0.9))
        self.resize(w, h)
        geo = self.frameGeometry()
        geo.moveCenter(screen.center())
        self.move(geo.topLeft())
        min_w = min(800, int(screen.width() * 0.5))
        min_h = min(600, int(screen.height() * 0.5))
        self.setMinimumSize(min_w, min_h)

        self.settings = QtCore.QSettings(
            str(SETTINGS_FILE), QtCore.QSettings.IniFormat
        )
        self._current_theme_name = "Modern"
        self._current_theme_tokens = get_theme_tokens(self._current_theme_name)
        self._font_size = self.settings.value("ui/font_size", 13, int)
        self.debug_mode = self.settings.value("ui/debug", False, bool)
        self.log_level = self.settings.value("log/level", "", str).upper()
        if not self.log_level:
            self.log_level = "DEBUG" if self.debug_mode else "INFO"
        self.large_controls = self.settings.value(
            "ui/large_controls", False, bool
        )
        self._apply_log_level(self.log_level)
        self.large_controls = self.settings.value(
            "ui/large_controls", False, bool
        )
        logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        self._audio_player = QtMultimedia.QMediaPlayer(self)
        self._audio_output = QtMultimedia.QAudioOutput(self)
        self._audio_player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(
            self.settings.value("ui/audio_preview_volume", 0.8, float)
        )
        self._audio_player.errorOccurred.connect(self._on_audio_preview_error)

        self._restore_window_state()
        self.setMinimumSize(900, 560)

        self.state = build_initial_state(
            Path(
                self._get_last_dir("ui/last_image_dir", default_downloads_dir())
            ),
            Path(
                self._get_last_dir("ui/last_audio_dir", default_downloads_dir())
            ),
        )

        sys.excepthook = self._global_exception

        self.pairs: List[PairItem] = []
        self.model = PairTableModel(self.pairs)
        self.plugin_manager = PluginManager(APP_DIR / "plugins")
        self.plugin_manager.load()
        logger.info(
            "Plugin-System aktiv. Geladene Plugins: %s",
            ", ".join(self.plugin_manager.loaded_plugins) or "keine",
        )

        ff_ok = check_ffmpeg()
        self.dashboard = InfoDashboard(UI_TEXTS)
        self.dashboard.set_env(ff_ok, True)
        if not ff_ok:
            self._show_error_dialog(
                "FFmpeg fehlt",
                "Bitte FFmpeg installieren oder im Setup reparieren, sonst kann kein Video erzeugt werden.",
                QtWidgets.QMessageBox.Warning,
            )

        self.image_list = ImageListWidget(
            "Bilder", (".jpg", ".jpeg", ".png", ".bmp", ".webp")
        )
        self.audio_list = AudioListWidget(
            "Audios", (".mp3", ".wav", ".flac", ".m4a", ".aac")
        )
        self.favorite_list = FavoriteListWidget(
            "Favoriten", (".jpg", ".jpeg", ".png", ".bmp", ".webp")
        )
        self.image_list.add_to_fav.connect(self._add_to_favorites)
        self.favorite_list.use_fav.connect(self._use_favorite)
        self.favorite_list.removed.connect(
            lambda p: self._log(f"Favorit entfernt: {p}")
        )
        self.image_list.files_dropped.connect(self._on_images_added)
        self.audio_list.files_dropped.connect(self._on_audios_added)
        self.image_list.itemSelectionChanged.connect(self._update_counts)
        self.audio_list.itemSelectionChanged.connect(self._update_counts)

        pool_tabs = QtWidgets.QTabWidget()
        pool_tabs.setAccessibleName("Datei-Register")
        pool_tabs.setAccessibleDescription(
            "Register für Bilder, Audios und Favoriten"
        )
        pool_tabs.addTab(self.image_list, "Bilder")
        pool_tabs.addTab(self.audio_list, "Audios")
        pool_tabs.addTab(self.favorite_list, "Favoriten")

        pool_box = QtWidgets.QGroupBox("Dateilisten")
        pb_lay = QtWidgets.QVBoxLayout(pool_box)
        pb_lay.addWidget(pool_tabs)

        # optionale Seitenleiste (Zusatzinfos)
        self.sidebar = QtWidgets.QDockWidget("Schnellhilfe", self)
        self.sidebar.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable)
        self.sidebar.setAllowedAreas(Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.sidebar)
        sidebar_hint = QtWidgets.QLabel(
            "Schnellhilfe: Im Hauptbereich sind jetzt 6 gleich große Workflow-Felder angeordnet."
        )
        sidebar_hint.setWordWrap(True)
        sidebar_hint.setMargin(8)
        self.sidebar.setWidget(sidebar_hint)
        self.sidebar.setVisible(
            self.settings.value("ui/show_sidebar", False, bool)
        )

        self.table = QtWidgets.QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._table_menu)
        self.table.setToolTip(
            "Doppelklick: Pfad bearbeiten, Rechtsklick für Menü"
        )
        self.table.setStatusTip(
            "Doppelklick: Pfad bearbeiten, Rechtsklick für Menü"
        )
        self.table.setAccessibleName("Paar-Tabelle")
        self.table.setAccessibleDescription("Liste der Bild- und Audio-Paare")
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setWordWrap(True)

        self.help_pane = HelpPane(self._current_theme_tokens)
        self.help_pane.setAccessibleName("Hilfe-Bereich")
        self.help_pane.setAccessibleDescription("Kurzanleitung zum Tool")

        # Einstellungen
        self.out_dir_edit = QtWidgets.QLineEdit(
            str(
                self.settings.value("encode/out_dir", default_output_dir(), str)
            )
        )
        self.out_dir_edit.setPlaceholderText("Zielordner für fertige Videos")
        self.out_dir_edit.setAccessibleName("Zielordner")
        self.out_dir_edit.setAccessibleDescription("Pfad für fertige Videos")
        self.btn_out_open = QtWidgets.QToolButton()
        self.btn_out_open.setText(self._ui_text("ui.buttons.open", "Öffnen"))
        self.btn_out_open.setToolTip(
            self._ui_text(
                "ui.tooltips.open_output_dir",
                "Ausgabeordner im Dateimanager öffnen",
            )
        )
        self.btn_out_open.setAccessibleName("Ordner öffnen")
        self.btn_out_open.setAccessibleDescription(
            "Ordner im Dateimanager anzeigen"
        )
        self.project_dir_edit = QtWidgets.QLineEdit(
            str(
                self.settings.value(
                    "project/default_dir", default_project_dir(), str
                )
            )
        )
        self.project_dir_edit.setPlaceholderText(
            "Standardordner für Projektdateien"
        )
        self.project_dir_edit.setAccessibleName("Standard-Projektordner")
        self.project_dir_edit.setAccessibleDescription(
            "Standardpfad für Projektdateien"
        )
        self.btn_project_dir = QtWidgets.QToolButton()
        self.btn_project_dir.setText(
            self._ui_text("ui.buttons.select", "Auswählen")
        )
        self.btn_project_dir.setToolTip(
            self._ui_text(
                "ui.tooltips.select_default_project_dir",
                "Standard-Projektordner auswählen",
            )
        )
        self.btn_project_dir.setAccessibleName("Projektordner auswählen")
        self.btn_project_dir.setAccessibleDescription(
            "Ordner für Projektdateien auswählen"
        )
        self.crf_spin = QtWidgets.QSpinBox()
        self.crf_spin.setRange(0, 51)
        self.crf_spin.setValue(self.settings.value("encode/crf", 23, int))
        self.crf_spin.setAccessibleName("CRF Qualität")
        self.crf_spin.setAccessibleDescription(
            "Qualität für das Video (0 bis 51)"
        )
        self.preset_combo = QtWidgets.QComboBox()
        self.preset_combo.addItems(
            [
                "ultrafast",
                "superfast",
                "veryfast",
                "faster",
                "fast",
                "medium",
                "slow",
                "slower",
                "veryslow",
            ]
        )
        self.preset_combo.setCurrentText(
            self.settings.value("encode/preset", "ultrafast", str)
        )
        self.preset_combo.setAccessibleName("Preset")
        self.preset_combo.setAccessibleDescription(
            "Geschwindigkeits-Voreinstellung für die Kodierung"
        )
        self.width_spin = QtWidgets.QSpinBox()
        self.width_spin.setRange(16, 7680)
        self.width_spin.setValue(self.settings.value("encode/width", 1920, int))
        self.width_spin.setAccessibleName("Video-Breite")
        self.width_spin.setAccessibleDescription("Breite des Videos in Pixel")
        self.height_spin = QtWidgets.QSpinBox()
        self.height_spin.setRange(16, 4320)
        self.height_spin.setValue(
            self.settings.value("encode/height", 1080, int)
        )
        self.height_spin.setAccessibleName("Video-Höhe")
        self.height_spin.setAccessibleDescription("Höhe des Videos in Pixel")
        self.abitrate_edit = QtWidgets.QLineEdit(
            self.settings.value("encode/abitrate", "192k", str)
        )
        self.abitrate_edit.setPlaceholderText("z.B. 192k")
        self.abitrate_edit.setAccessibleName("Audio-Bitrate")
        self.abitrate_edit.setAccessibleDescription(
            "Audioqualität als Bitrate, zum Beispiel 192k"
        )
        self.output_template_edit = QtWidgets.QLineEdit(
            self.settings.value(
                "encode/output_template",
                "{audio_name}_{video_laenge}_{zeitstempel}_{qualitaet}_{abmasse}_{form}.mp4",
                str,
            )
        )
        self.output_template_edit.setPlaceholderText(
            "{audio_name}_{video_laenge}_{zeitstempel}_{qualitaet}_{abmasse}_{form}.mp4"
        )
        self.output_template_edit.setAccessibleName("Dateinamen-Template")
        self.output_template_edit.setAccessibleDescription(
            "Vorlage für Ausgabedateien"
        )
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(
            ["Standard", "Slideshow", "Video + Audio", "Mehrere Audios, 1 Bild"]
        )
        self.mode_combo.setToolTip(
            self._ui_text(
                "ui.tooltips.processing_mode", "Verarbeitungsmodus wählen"
            )
        )
        self.mode_combo.setCurrentText(
            self.settings.value("encode/mode", "Standard", str)
        )
        self.mode_combo.setAccessibleName("Modus")
        self.mode_combo.setAccessibleDescription(
            "Auswahl des Verarbeitungsmodus"
        )
        max_parallel = max(1, os.cpu_count() or 4)
        self.parallel_jobs_spin = QtWidgets.QSpinBox()
        self.parallel_jobs_spin.setRange(1, max_parallel)
        self.parallel_jobs_spin.setValue(
            self.settings.value("encode/parallel_jobs", 1, int)
        )
        self.parallel_jobs_spin.setAccessibleName("Parallelität")
        self.parallel_jobs_spin.setAccessibleDescription(
            "Anzahl paralleler Jobs"
        )
        self.clear_after = QtWidgets.QCheckBox(
            "Nach Fertigstellung Listen leeren"
        )
        self.clear_after.setChecked(
            self.settings.value("ui/clear_after", False, bool)
        )
        self.auto_open_output = QtWidgets.QCheckBox(
            "Ausgabeordner nach Fertigstellung öffnen"
        )
        self.auto_open_output.setChecked(
            self.settings.value("ui/auto_open_output", True, bool)
        )
        self.auto_open_output.setAccessibleName(
            "Ausgabeordner automatisch öffnen"
        )
        self.mode_combo.setAccessibleDescription(
            "Auswahl des Verarbeitungsmodus"
        )
        self.auto_open_output.setAccessibleDescription(
            "Öffnet den Ausgabeordner nach Abschluss der Erstellung"
        )
        self.auto_save_project = QtWidgets.QCheckBox(
            "Projekt beim Start/Schließen automatisch sichern"
        )
        self.auto_save_project.setChecked(
            self.settings.value("ui/auto_save_project", False, bool)
        )
        self.auto_save_project.setAccessibleName("Projekt automatisch sichern")
        self.auto_save_project.setAccessibleDescription(
            "Sichert den aktuellen Stand automatisch beim Start und Schließen"
        )
        self.clear_after.setAccessibleName("Listen automatisch leeren")
        self.clear_after.setAccessibleDescription(
            "Nach dem Abschluss alle Listen leeren"
        )

        self.font_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.font_slider.setRange(10, 36)
        self.font_slider.setValue(self._font_size)
        self.font_slider.setAccessibleName("Schriftgrößen-Schieber")
        self.font_slider.setAccessibleDescription(
            "Schriftgröße der Oberfläche einstellen"
        )
        self.font_value_label = QtWidgets.QLabel(str(self._font_size))
        self.font_value_label.setAccessibleName("Schriftgröße Anzeige")
        self.font_slider.valueChanged.connect(self._on_font_slider_changed)
        self.large_controls_toggle = QtWidgets.QCheckBox(
            "Große Bedienelemente (besser klickbar)"
        )
        self.large_controls_toggle.setChecked(self.large_controls)
        self.large_controls_toggle.setToolTip(
            "Buttons, Tabellenzeilen und Text etwas größer"
        )
        self.large_controls_toggle.toggled.connect(self._toggle_large_controls)
        self.log_level_combo = QtWidgets.QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText(self.log_level)
        self.log_level_combo.setAccessibleName("Protokollstufe")
        self.log_level_combo.setAccessibleDescription(
            "Protokollierungsstufe auswählen"
        )
        self.language_combo = QtWidgets.QComboBox()
        self.language_combo.addItems(
            [
                "Deutsch (Standard)",
                "Polski (informacje)",
                "Englisch (vorbereitet)",
            ]
        )
        self.language_combo.setCurrentText(
            self.settings.value("ui/language", "Deutsch (Standard)", str)
        )
        self.language_combo.setAccessibleName("Sprache")
        self.language_combo.setAccessibleDescription("Sprache vorbereiten")
        self.spacing_combo = QtWidgets.QComboBox()
        self.spacing_combo.addItems(
            ["Kompakt", "Standard", "Großzügig", "Barrierefrei"]
        )
        self.spacing_combo.setCurrentText(
            self.settings.value("ui/spacing_profile", "Standard", str)
        )
        self.spacing_combo.setAccessibleName("Abstände")
        self.spacing_combo.setAccessibleDescription(
            "Abstand zwischen Feldern und Schaltflächen"
        )
        self.interface_combo = QtWidgets.QComboBox()
        self.interface_combo.addItems(
            [
                "Standard",
                "Profi",
                "Seniorenfreundlich",
                "Barrierefrei Max",
            ]
        )
        self.interface_combo.setCurrentText(
            self.settings.value("ui/interface_profile", "Standard", str)
        )
        self.interface_combo.setAccessibleName("Interface-Profil")
        self.interface_combo.setAccessibleDescription(
            "Standard, Profi oder Seniorenfreundlich für klare Abstände und große Klickflächen"
        )
        self.fallback_enabled = QtWidgets.QCheckBox(
            "Fallback-Medien bei Fehlern automatisch nutzen"
        )
        self.fallback_enabled.setChecked(
            self.settings.value("fallback/enabled", True, bool)
        )
        self.btn_fallback_media = QtWidgets.QPushButton(
            "Fallback-Medien verwalten"
        )
        self.btn_fallback_media.setToolTip(
            "Persistentes Ersatzbild und bis zu zwei Ersatz-Audios hinterlegen"
        )

        form = QtWidgets.QFormLayout()
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        form.setRowWrapPolicy(QtWidgets.QFormLayout.WrapLongRows)
        form.setFormAlignment(Qt.AlignTop | Qt.AlignLeft)
        form.setLabelAlignment(Qt.AlignTop | Qt.AlignLeft)
        out_wrap_layout = QtWidgets.QHBoxLayout()
        out_wrap_layout.setContentsMargins(0, 0, 0, 0)
        out_wrap_layout.addWidget(self.out_dir_edit)
        out_wrap_layout.addWidget(self.btn_out_open)
        out_wrap = QtWidgets.QWidget()
        out_wrap.setLayout(out_wrap_layout)
        project_wrap_layout = QtWidgets.QHBoxLayout()
        project_wrap_layout.setContentsMargins(0, 0, 0, 0)
        project_wrap_layout.addWidget(self.project_dir_edit)
        project_wrap_layout.addWidget(self.btn_project_dir)
        project_wrap = QtWidgets.QWidget()
        project_wrap.setLayout(project_wrap_layout)
        self._add_form(form, "Ausgabeordner", out_wrap, "Zielordner für MP4s")
        self._add_form(
            form,
            "Standard-Projektordner",
            project_wrap,
            "Standardordner für Projekte",
        )
        self._add_form(
            form, "CRF", self.crf_spin, "Qualität (0=lossless, 23=Standard)"
        )
        self._add_form(
            form,
            "Preset",
            self.preset_combo,
            "x264 Preset (schneller = größere Datei)",
        )
        self._add_form(form, "Breite", self.width_spin, "Video-Breite in Pixel")
        self._add_form(form, "Höhe", self.height_spin, "Video-Höhe in Pixel")
        self._add_form(
            form, "Audio-Bitrate", self.abitrate_edit, "z.B. 192k, 256k"
        )
        template_row = QtWidgets.QHBoxLayout()
        template_row.setContentsMargins(0, 0, 0, 0)
        template_row.addWidget(self.output_template_edit, 1)
        self.template_presets_combo = QtWidgets.QComboBox()
        self.template_presets_combo.addItems(
            [
                "Template-Presets",
                "Standard kompakt",
                "Mit Qualität+Maße",
                "Mit Datum+Uhrzeit",
            ]
        )
        self.template_presets_combo.setAccessibleName("Template-Presets")
        self.template_presets_combo.currentTextChanged.connect(
            self._apply_template_preset
        )
        template_row.addWidget(self.template_presets_combo)
        template_wrap = QtWidgets.QWidget()
        template_wrap.setLayout(template_row)
        self._add_form(
            form,
            "Dateinamen-Template",
            template_wrap,
            "Preset statt Freitext nutzen: {audio_stem}, {zeitstempel}, {qualitaet}, {abmasse}",
        )
        self._add_form(
            form, "Modus", self.mode_combo, "z.B. Slideshow oder Video + Audio"
        )
        self._add_form(
            form,
            "Parallelität (Jobs)",
            self.parallel_jobs_spin,
            "Anzahl paralleler Jobs",
        )
        self._add_form(
            form,
            "Protokoll-Stufe",
            self.log_level_combo,
            "DETAILS für das Protokoll wählen",
        )
        self._add_form(
            form, "Sprache", self.language_combo, "Sprachwahl vorbereiten"
        )
        self._add_form(
            form,
            "Abstände",
            self.spacing_combo,
            "Kompakt, Standard oder großzügig",
        )
        self._add_form(
            form,
            "Interface-Profil",
            self.interface_combo,
            "Standard, Profi oder Seniorenfreundlich (extra groß und laienfreundlich)",
        )
        self._add_form(
            form,
            "Fehler-Fallback",
            self.fallback_enabled,
            "Bei ungültigen Dateien auf hinterlegte Medien ausweichen",
        )
        self._add_form(
            form,
            "Fallback-Medien",
            self.btn_fallback_media,
            "Bild + bis zu 2 Audios persistent speichern",
        )
        font_row = QtWidgets.QHBoxLayout()
        font_row.setContentsMargins(0, 0, 0, 0)
        font_row.addWidget(self.font_slider)
        font_row.addWidget(self.font_value_label)
        font_wrap = QtWidgets.QWidget()
        font_wrap.setLayout(font_row)
        self._add_form(
            form,
            "Schriftgröße",
            font_wrap,
            "Schriftgröße der Oberfläche anpassen",
        )
        form.addRow("", self.clear_after)
        form.addRow("", self.auto_open_output)
        form.addRow("", self.auto_save_project)
        form.addRow("", self.large_controls_toggle)

        settings_box = QtWidgets.QGroupBox("Einstellungen")
        settings_content = QtWidgets.QWidget()
        settings_content.setLayout(form)
        settings_scroll = QtWidgets.QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        settings_scroll.setWidget(settings_content)
        settings_layout = QtWidgets.QVBoxLayout(settings_box)
        settings_layout.setContentsMargins(6, 6, 6, 6)
        settings_layout.addWidget(settings_scroll)
        self.settings_scroll = settings_scroll

        self.settings_widget = settings_box

        table_box = QtWidgets.QGroupBox("Paare")
        tb_lay = QtWidgets.QVBoxLayout(table_box)
        tb_lay.addWidget(self.table)

        help_box = QtWidgets.QGroupBox("Hilfe")
        hb_lay = QtWidgets.QVBoxLayout(help_box)
        hb_lay.addWidget(self.help_pane)
        self.help_box = help_box

        self.structure_tree = QtWidgets.QTreeWidget()
        self.structure_tree.setHeaderLabels(["Pfad"])
        self.structure_tree.setAlternatingRowColors(True)
        self.structure_tree.setAccessibleName("Projektstruktur")
        self.structure_tree.setAccessibleDescription(
            "Baumansicht für Bilder, Audios und Output"
        )
        self.structure_filter = QtWidgets.QComboBox()
        self.structure_filter.addItems(["Alles", "Bilder", "Audios", "Output"])
        self.structure_filter.setAccessibleName("Struktur-Filter")
        self.structure_filter.setAccessibleDescription(
            "Filtert die Projektstruktur nach Bereich"
        )
        self.structure_search = QtWidgets.QLineEdit()
        self.structure_search.setPlaceholderText(
            "Pfad-Filter, z. B. /Projekt oder Ferien"
        )
        self.structure_search.setAccessibleName("Pfad-Filter")
        self.structure_search.setAccessibleDescription(
            "Filtert die Projektstruktur nach Text im Pfad"
        )
        self.structure_clear_btn = QtWidgets.QToolButton()
        self.structure_clear_btn.setText("X")
        self.structure_clear_btn.setToolTip(
            self._ui_text(
                "ui.tooltips.clear_path_filter", "Pfad-Filter löschen"
            )
        )
        self.structure_clear_btn.setAccessibleName("Pfad-Filter löschen")
        self.structure_clear_btn.clicked.connect(
            lambda: self.structure_search.setText("")
        )

        structure_filter_row = QtWidgets.QHBoxLayout()
        structure_filter_row.setContentsMargins(0, 0, 0, 0)
        structure_filter_row.addWidget(QtWidgets.QLabel("Filter"))
        structure_filter_row.addWidget(self.structure_filter)
        structure_filter_row.addWidget(QtWidgets.QLabel("Suche"))
        structure_filter_row.addWidget(self.structure_search, 1)
        structure_filter_row.addWidget(self.structure_clear_btn)

        structure_box = QtWidgets.QGroupBox("Projektstruktur")
        structure_layout = QtWidgets.QVBoxLayout(structure_box)
        structure_layout.addLayout(structure_filter_row)
        structure_layout.addWidget(self.structure_tree)

        self.progress_total = QtWidgets.QProgressBar()
        self.progress_total.setFormat("%p% gesamt")
        self.progress_total.setAccessibleName("Gesamtfortschritt")
        self.progress_total.setAccessibleDescription(
            "Fortschritt aller Aufgaben"
        )
        self.log_path_label = QtWidgets.QLabel("Log-Pfad:")
        self.log_path_label.setAccessibleName("Log-Pfad Label")
        self.log_path_edit = QtWidgets.QLineEdit(str(LOG_DIR))
        self.log_path_edit.setReadOnly(True)
        self.log_path_edit.setAccessibleName("Log-Pfad")
        self.log_path_edit.setAccessibleDescription(
            "Speicherort der Logdateien"
        )
        self.log_path_edit.setToolTip(
            self._ui_text(
                "ui.tooltips.log_files_location",
                "Speicherort der Protokolldateien",
            )
        )
        self.log_path_btn = QtWidgets.QPushButton("Pfad kopieren")
        self.log_path_btn.setToolTip(
            "Log-Ordner in die Zwischenablage kopieren"
        )
        self.log_path_btn.clicked.connect(self._copy_log_path)
        log_path_row = QtWidgets.QHBoxLayout()
        log_path_row.addWidget(self.log_path_label)
        log_path_row.addWidget(self.log_path_edit, 1)
        log_path_row.addWidget(self.log_path_btn)
        self.log_edit = QtWidgets.QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMaximumBlockCount(5000)
        self.log_edit.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
        self.log_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.log_edit.setAccessibleName("Protokoll")
        self.log_edit.setAccessibleDescription(
            "Fortlaufende Meldungen des Programms"
        )

        self.log_box = QtWidgets.QGroupBox("Protokoll")
        bl = QtWidgets.QVBoxLayout(self.log_box)
        bl.addWidget(self.progress_total)
        bl.addLayout(log_path_row)
        bl.addWidget(self.log_edit)

        # Buttons
        action_buttons = create_action_buttons(
            self,
            on_timer_tick=self._toggle_encode_ready_style,
        )
        self.btn_add_images = action_buttons.buttons["add_images"]
        self.btn_add_audios = action_buttons.buttons["add_audios"]
        self.btn_auto_pair = action_buttons.buttons["auto_pair"]
        self.btn_clear = action_buttons.buttons["clear"]
        self.btn_undo = action_buttons.buttons["undo"]
        self.btn_save = action_buttons.buttons["save"]
        self.btn_load = action_buttons.buttons["load"]
        self.btn_encode = action_buttons.buttons["encode"]
        self.btn_stop = action_buttons.buttons["stop"]
        self.btn_wizard = action_buttons.buttons["wizard"]
        self._encode_ready_timer = action_buttons.timer
        self._encode_ready_on = False
        self.top_buttons_layout = action_buttons.layout
        self._action_button_wrappers = action_buttons.wrappers
        self._reflow_action_buttons(available_width=0)
        self.btn_box = action_buttons.box

        dashboard_header = QtWidgets.QGroupBox("DashboardHeader")
        dashboard_header_layout = QtWidgets.QVBoxLayout(dashboard_header)
        dashboard_header_layout.setContentsMargins(8, 8, 8, 8)
        dashboard_header_layout.addWidget(self.dashboard)

        self.workflow_columns = QtWidgets.QSplitter(Qt.Horizontal)
        self.workflow_columns.setChildrenCollapsible(False)
        self.workflow_columns.setHandleWidth(10)
        col1 = QtWidgets.QSplitter(Qt.Vertical)
        col1.setChildrenCollapsible(False)
        col1.setHandleWidth(10)
        col1.addWidget(pool_box)
        col1.addWidget(self.settings_widget)
        col2 = QtWidgets.QSplitter(Qt.Vertical)
        col2.setChildrenCollapsible(False)
        col2.setHandleWidth(10)
        col2.addWidget(self.btn_box)
        col2.addWidget(table_box)
        col3 = QtWidgets.QSplitter(Qt.Vertical)
        col3.setChildrenCollapsible(False)
        col3.setHandleWidth(10)
        col3.addWidget(help_box)
        col3.addWidget(self.log_box)
        self.workflow_columns.addWidget(col1)
        self.workflow_columns.addWidget(col2)
        self.workflow_columns.addWidget(col3)
        self.workflow_columns.setSizes([1, 1, 1])
        for idx in range(3):
            self.workflow_columns.setCollapsible(idx, False)
        for col in (col1, col2, col3):
            col.setSizes([1, 1])
            col.setCollapsible(0, False)
            col.setCollapsible(1, False)
        self.workflow_splitters = [col1, col2, col3]

        for section in (
            pool_box,
            self.settings_widget,
            self.btn_box,
            table_box,
            help_box,
            self.log_box,
        ):
            section.setMinimumSize(
                self.WORKFLOW_SECTION_MIN_WIDTH,
                self.WORKFLOW_SECTION_MIN_HEIGHT,
            )
        self._workflow_sections = (
            pool_box,
            self.settings_widget,
            self.btn_box,
            table_box,
            help_box,
            self.log_box,
        )

        central_layout = QtWidgets.QVBoxLayout()
        central_layout.addWidget(dashboard_header)
        self.focus_hint_label = QtWidgets.QLabel(
            "Tipp: Wählen Sie ein Farbschema mit hohem Kontrast. Der aktive Bereich wird größer und bleibt klar fokussiert (Fokus = sichtbare Hervorhebung)."
        )
        self.focus_hint_label.setAccessibleName("Hinweis aktiver Bereich")
        self.focus_hint_label.setWordWrap(True)
        central_layout.addWidget(self.focus_hint_label)
        central_layout.addWidget(self.workflow_columns, 1)
        self.central_layout = central_layout
        central = QtWidgets.QWidget()
        central.setLayout(central_layout)
        self.setCentralWidget(central)

        self.count_label = QtWidgets.QLabel(
            text_with_fallback(
                UI_TEXTS,
                "statusbar.counts",
                "{images} Bilder | {audios} Audios | {pairs} Paare | Auswahl: {selected_images}B/{selected_audios}A",
            ).format(
                images=0,
                audios=0,
                pairs=0,
                selected_images=0,
                selected_audios=0,
            )
        )
        self.statusBar().addPermanentWidget(self.count_label)

        self.copy_only = False
        self._build_menus()
        self._toggle_help(self.act_show_help.isChecked())
        self._toggle_log(self.act_show_log.isChecked())

        self._history: List[List[PairItem]] = []
        self.thread: Optional[QtCore.QThread] = None
        self.worker: Optional[EncodeWorker] = None

        # Signals
        self.btn_add_images.clicked.connect(self._pick_images)
        self.btn_add_audios.clicked.connect(self._pick_audios)
        self.btn_auto_pair.clicked.connect(self._auto_pair)
        self.btn_clear.clicked.connect(self._clear_all)
        self.btn_undo.clicked.connect(self._undo_last)
        self.btn_save.clicked.connect(self._save_project)
        self.btn_load.clicked.connect(self._load_project)
        self.btn_encode.clicked.connect(self._start_encode)
        self.btn_stop.clicked.connect(self._stop_encode)
        self.btn_wizard.clicked.connect(self._show_guided_wizard)
        self.table.doubleClicked.connect(self._show_statusbar_path)
        self.btn_out_open.clicked.connect(self._open_out_dir)
        self.btn_project_dir.clicked.connect(self._pick_default_project_dir)
        self.project_dir_edit.editingFinished.connect(
            self._validate_project_dir
        )
        self.output_template_edit.editingFinished.connect(
            self._validate_output_template
        )
        self.log_level_combo.currentTextChanged.connect(self._update_log_level)
        self.language_combo.currentTextChanged.connect(self._update_language)
        self.btn_fallback_media.clicked.connect(self._manage_fallback_media)
        self.spacing_combo.currentTextChanged.connect(
            self._update_spacing_profile
        )
        self.interface_combo.currentTextChanged.connect(
            self._update_interface_profile
        )
        self.auto_open_output.toggled.connect(self._toggle_auto_open_output)
        self.auto_save_project.toggled.connect(self._toggle_auto_save_project)
        self.mode_combo.currentTextChanged.connect(self._update_default_mode)
        self.parallel_jobs_spin.valueChanged.connect(self._update_parallel_jobs)
        self.structure_filter.currentTextChanged.connect(
            self._apply_structure_filter
        )
        self.structure_search.textChanged.connect(self._apply_structure_filter)
        self.out_dir_edit.editingFinished.connect(self._refresh_structure_view)

        self._set_font(self._font_size)
        self._apply_theme(self.settings.value("ui/theme", "Modern"))
        self._apply_spacing_profile(self.spacing_combo.currentText())
        self._apply_interface_profile(self.interface_combo.currentText())
        self.restoreGeometry(self.settings.value("ui/geometry", b"", bytes))
        self.restoreState(self.settings.value("ui/window_state", b"", bytes))
        QtGui.QShortcut(QtGui.QKeySequence("F1"), self).activated.connect(
            self._show_help_window
        )
        if self.auto_save_project.isChecked():
            self._auto_save_project("Start")
        QtGui.QShortcut(QtGui.QKeySequence("F5"), self).activated.connect(
            self._start_encode
        )
        self._refresh_structure_view()
        self._section_boxes = {
            "Dateilisten": pool_box,
            "Paare": table_box,
            "Hilfe": help_box,
            "Protokoll": self.log_box,
            "Einstellungen": settings_box,
            "Aktionen": self.btn_box,
        }
        self._section_resize_targets = {
            "Dateilisten": (0, 0),
            "Einstellungen": (0, 1),
            "Aktionen": (1, 0),
            "Paare": (1, 1),
            "Hilfe": (2, 0),
            "Protokoll": (2, 1),
        }
        QtWidgets.QApplication.instance().focusChanged.connect(
            self._on_focus_changed
        )
        self._active_section_name = "Paare"
        self._on_focus_changed(None, self.table)

    # ----- UI helpers -----
    def _ui_text(self, key: str, fallback: str) -> str:
        return text_with_fallback(UI_TEXTS, key, fallback)

    def _build_menus(self):
        menubar = self.menuBar()

        m_datei = menubar.addMenu("Datei")
        act_project_root = QAction("Projektordner wählen", self)
        act_project_root.setToolTip(
            self._ui_text(
                "menu.tooltips.project_root",
                "Startordner für Dialoge festlegen",
            )
        )
        act_project_root.triggered.connect(self._choose_project_root)
        m_datei.addAction(act_project_root)
        act_load = QAction("Projekt laden", self)
        act_load.setToolTip(
            self._ui_text(
                "menu.tooltips.load_project", "Gespeichertes Projekt laden"
            )
        )
        act_load.setShortcut(QtGui.QKeySequence("Ctrl+O"))
        act_load.triggered.connect(self._load_project)
        m_datei.addAction(act_load)
        act_save = QAction("Projekt speichern", self)
        act_save.setToolTip(
            self._ui_text("menu.tooltips.save_project", "Projekt sichern")
        )
        act_save.setShortcut(QtGui.QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self._save_project)
        m_datei.addAction(act_save)
        act_quit = QAction("Beenden", self)
        act_quit.setToolTip(
            self._ui_text("menu.tooltips.quit_app", "Programm schließen")
        )
        act_quit.triggered.connect(self.close)
        m_datei.addAction(act_quit)

        m_ansicht = menubar.addMenu("Ansicht")
        act_font_plus = QAction("Schrift +", self)
        act_font_plus.setToolTip(
            self._ui_text("menu.tooltips.font_increase", "Schriftgröße erhöhen")
        )
        act_font_plus.triggered.connect(lambda: self._change_font(1))
        act_font_minus = QAction("Schrift -", self)
        act_font_minus.setToolTip(
            self._ui_text(
                "menu.tooltips.font_decrease", "Schriftgröße verkleinern"
            )
        )
        act_font_minus.triggered.connect(lambda: self._change_font(-1))
        act_font_reset = QAction("Schrift Reset", self)
        act_font_reset.setToolTip(
            self._ui_text(
                "menu.tooltips.font_reset", "Schriftgröße zurücksetzen"
            )
        )
        act_font_reset.triggered.connect(lambda: self._set_font(13))
        m_ansicht.addActions([act_font_plus, act_font_minus, act_font_reset])
        self.act_show_help = QAction(
            "Hilfe-Bereich",
            self,
            checkable=True,
            checked=self.settings.value("ui/show_help", True, bool),
        )
        self.act_show_help.toggled.connect(self._toggle_help)
        m_ansicht.addAction(self.act_show_help)
        self.act_show_log = QAction(
            "Log-Bereich",
            self,
            checkable=True,
            checked=self.settings.value("ui/show_log", True, bool),
        )
        self.act_show_log.toggled.connect(self._toggle_log)
        m_ansicht.addAction(self.act_show_log)
        self.act_show_sidebar = QAction(
            "Sidebar", self, checkable=True, checked=self.sidebar.isVisible()
        )
        self.act_show_sidebar.toggled.connect(self._toggle_sidebar)
        m_ansicht.addAction(self.act_show_sidebar)

        m_theme = menubar.addMenu("Farbschema")
        for name in THEMES.keys():
            act = QAction(name, self)
            act.triggered.connect(lambda _=False, n=name: self._apply_theme(n))
            m_theme.addAction(act)

        m_option = menubar.addMenu("Optionen")
        self.act_copy_only = QAction(
            "Dateien nur kopieren (nicht verschieben)",
            self,
            checkable=True,
            checked=self.copy_only,
        )
        self.act_copy_only.setToolTip(
            self._ui_text("menu.tooltips.copy_only", "Originaldateien behalten")
        )
        self.act_copy_only.triggered.connect(self._toggle_copy_mode)
        m_option.addAction(self.act_copy_only)
        self.act_debug = QAction(
            "Debug-Log", self, checkable=True, checked=self.debug_mode
        )
        self.act_debug.setToolTip(
            self._ui_text(
                "menu.tooltips.enable_debug_log",
                "Detailiertes Protokoll aktivieren",
            )
        )
        self.act_debug.triggered.connect(self._toggle_debug)
        m_option.addAction(self.act_debug)

        m_hilfe = menubar.addMenu("Hilfe")
        act_doc = QAction("README öffnen", self)
        act_doc.setToolTip(
            self._ui_text(
                "menu.tooltips.show_documentation",
                "Dokumentation anzeigen",
            )
        )
        act_doc.triggered.connect(self._open_readme)
        act_log = QAction("Logdatei öffnen", self)
        act_log.setToolTip(
            self._ui_text(
                "menu.tooltips.show_latest_logs",
                "Letzte Meldungen anzeigen",
            )
        )
        act_log.triggered.connect(self._open_logfile)
        act_help = QAction("Kurzanleitung", self)
        act_help.setToolTip(
            self._ui_text(
                "menu.tooltips.show_quick_help",
                "Kurzes Hilfefenster anzeigen",
            )
        )
        act_help.triggered.connect(self._show_help_window)
        act_wizard = QAction("Geführter Start", self)
        act_wizard.setToolTip(
            self._ui_text(
                "menu.tooltips.open_guided_wizard",
                "Schritt-für-Schritt-Assistent öffnen",
            )
        )
        act_wizard.triggered.connect(self._show_guided_wizard)
        m_hilfe.addAction(act_doc)
        m_hilfe.addAction(act_log)
        m_hilfe.addAction(act_help)
        m_hilfe.addAction(act_wizard)

    def _change_font(self, delta: int):
        self._set_font(self._font_size + delta)

    def _on_font_slider_changed(self, value: int):
        self.font_value_label.setText(str(value))
        self._set_font(value)

    def _set_font(self, size: int):
        size = max(10, min(36, size))
        self._font_size = size
        self._apply_font()
        if hasattr(self, "font_slider") and self.font_slider.value() != size:
            self.font_slider.setValue(size)
        if hasattr(self, "font_value_label"):
            self.font_value_label.setText(str(size))
        self.settings.setValue("ui/font_size", size)
        self._update_workflow_section_constraints()
        self._log(f"Schriftgröße gesetzt auf {size}")

    def _apply_font(self):
        f = QtGui.QFont("DejaVu Sans", self._font_size)
        self.setFont(f)

    def _apply_theme(self, name: str):
        if name not in THEMES:
            name = "Modern"
        css = THEMES.get(name, "")
        self._current_theme_name = name
        self._current_theme_tokens = get_theme_tokens(name)
        QtWidgets.QApplication.instance().setStyleSheet(css)
        self.settings.setValue("ui/theme", name)
        if hasattr(self, "help_pane"):
            self.help_pane.set_theme_tokens(self._current_theme_tokens)
        self._sync_encode_button_state()
        self._log(f"Farbschema gewechselt: {name}")

    def _sync_encode_button_state(self) -> None:
        if not hasattr(self, "btn_encode"):
            return
        self.btn_encode.setProperty("accentRole", "primaryAction")
        if self._encode_ready_timer.isActive():
            pulse = "a" if self._encode_ready_on else "b"
        else:
            pulse = "off"
        self.btn_encode.setProperty("readyPulse", pulse)
        self.btn_encode.style().unpolish(self.btn_encode)
        self.btn_encode.style().polish(self.btn_encode)
        self.btn_encode.update()

    def _rebalance_workflow_layout(
        self, active_name: Optional[str] = None
    ) -> None:
        if not hasattr(self, "workflow_columns"):
            return
        name = active_name or getattr(self, "_active_section_name", "Paare")
        active_column = self._section_resize_targets.get(name, (1, 1))[0]
        total = max(self.workflow_columns.width(), 1)
        base = max(self.WORKFLOW_SECTION_MIN_WIDTH, int(total * 0.28))
        focus = max(self.WORKFLOW_SECTION_MIN_WIDTH + 20, int(total * 0.38))
        column_sizes = [base, base, base]
        column_sizes[active_column] = focus
        self.workflow_columns.setSizes(column_sizes)

        total_h = max(self.workflow_columns.height(), 1)
        base_h = max(self.WORKFLOW_SECTION_MIN_HEIGHT, int(total_h * 0.44))
        focus_h = max(
            self.WORKFLOW_SECTION_MIN_HEIGHT + 20, int(total_h * 0.56)
        )
        for idx, splitter in enumerate(self.workflow_splitters):
            if idx == active_column:
                row = self._section_resize_targets.get(name, (idx, 0))[1]
                sizes = [base_h, base_h]
                sizes[row] = focus_h
                splitter.setSizes(sizes)
            else:
                splitter.setSizes([base_h, base_h])

    def _apply_template_preset(self, preset_name: str) -> None:
        presets = {
            "Standard kompakt": "{audio_stem}_{stamp}.mp4",
            "Mit Qualität+Maße": (
                "{audio_stem}_{video_laenge}_{qualitaet}_{abmasse}_{stamp}.mp4"
            ),
            "Mit Datum+Uhrzeit": (
                "{audio_stem}_{date}_{time}_{video_laenge}_{abmasse}.mp4"
            ),
        }
        template = presets.get(preset_name)
        if not template:
            return
        self.output_template_edit.setText(template)
        self._validate_output_template()
        self._log(f"Template-Preset gesetzt: {preset_name}")

    def _resize_focus_sections(self, active_name: str) -> None:
        self._active_section_name = active_name
        self._rebalance_workflow_layout(active_name)

    def _on_focus_changed(
        self,
        _old: Optional[QtWidgets.QWidget],
        now: Optional[QtWidgets.QWidget],
    ) -> None:
        active_name = ""
        for name, box in self._section_boxes.items():
            is_active = bool(now and box.isAncestorOf(now))
            box.setProperty("activeSection", is_active)
            box.style().unpolish(box)
            box.style().polish(box)
            box.update()
            if is_active:
                active_name = name
        if active_name:
            self._resize_focus_sections(active_name)
            self.focus_hint_label.setText(
                f"Aktiver Bereich: {active_name}. Tipp: Erst hier arbeiten, dann den nächsten Schritt starten."
            )

    def _apply_log_level(self, level_name: str) -> None:
        level_name = (level_name or "INFO").upper()
        if level_name not in ("DEBUG", "INFO", "WARNING", "ERROR"):
            level_name = "INFO"
        self.log_level = level_name
        level = getattr(logging, level_name, logging.INFO)
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        for handler in root_logger.handlers:
            handler.setLevel(level)
        self.debug_mode = level_name == "DEBUG"
        self.settings.setValue("log/level", level_name)
        self.settings.setValue("ui/debug", self.debug_mode)
        if (
            hasattr(self, "log_level_combo")
            and self.log_level_combo.currentText() != level_name
        ):
            self.log_level_combo.blockSignals(True)
            self.log_level_combo.setCurrentText(level_name)
            self.log_level_combo.blockSignals(False)
        if hasattr(self, "act_debug"):
            self.act_debug.setChecked(self.debug_mode)

    def _open_out_dir(self):
        path = self.out_dir_edit.text().strip()
        if not path:
            self._log("Ausgabeordner fehlt.", logging.WARNING)
            QtWidgets.QMessageBox.information(
                self,
                self._ui_text(
                    "dialogs.output_dir_missing.title",
                    "Ausgabeordner fehlt",
                ),
                self._ui_text(
                    "dialogs.output_dir_missing.body",
                    "Bitte zuerst einen Ausgabeordner festlegen.",
                ),
            )
            return
        out_path = Path(path).expanduser()
        try:
            out_path.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError, ValueError) as exc:
            logger.exception(
                "ui.output_dir_prepare_failed",
                extra={"path": str(out_path), "error": str(exc)},
            )
            self._log(
                f"Ausgabeordner konnte nicht erstellt werden: {exc}",
                logging.ERROR,
            )
            QtWidgets.QMessageBox.critical(
                self,
                self._ui_text(
                    "dialogs.output_dir_invalid.title",
                    "Ausgabeordner fehlerhaft",
                ),
                "Ordner konnte nicht erstellt werden.\n"
                "Ursache: fehlende Rechte oder ungültiger Pfad.\n"
                "Nächster Schritt: anderen Ordner wählen oder Rechte prüfen.\n"
                f"Befehl: ls -ld '{out_path}'\n\n"
                f"Technik-Detail: {exc}",
            )
            return
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(out_path)))
        self._log(f"Ausgabeordner geöffnet: {out_path}")

    def _open_readme(self):
        path = str(Path("README.md").resolve())
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
        self._log("README geöffnet")

    def _open_logfile(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(LOG_FILE)))
        self._log("Logdatei geöffnet")

    def _pick_default_project_dir(self):
        start_dir = self.project_dir_edit.text().strip() or str(
            default_project_dir()
        )
        selected = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            self._ui_text(
                "dialogs.default_project_dir.title",
                "Standard-Projektordner auswählen",
            ),
            start_dir,
        )
        if not selected:
            return
        self.project_dir_edit.setText(selected)
        self._validate_project_dir()

    def _validate_project_dir(self):
        value = self.project_dir_edit.text().strip()
        if not value:
            return
        path = Path(value).expanduser()
        try:
            path.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError, ValueError) as exc:
            logger.exception(
                "ui.project_dir_prepare_failed",
                extra={"path": str(path), "error": str(exc)},
            )
            QtWidgets.QMessageBox.warning(
                self,
                self._ui_text(
                    "dialogs.project_dir_invalid.title",
                    "Projektordner ungültig",
                ),
                "Der Ordner konnte nicht erstellt werden.\n"
                "Ursache: kein Zugriff oder ungültiger Pfad.\n"
                "Nächster Schritt: anderen Ordner wählen.\n"
                f"Befehl: mkdir -p '{path}'\n\n"
                f"Technik-Detail: {exc}",
            )
            self._log(f"Standard-Projektordner ungültig: {exc}", logging.ERROR)
            fallback = str(default_project_dir())
            self.project_dir_edit.setText(fallback)
            self.settings.setValue("project/default_dir", fallback)
            return
        self.settings.setValue("project/default_dir", str(path))
        self._log(f"Standard-Projektordner gesetzt: {path}")

    def _copy_log_path(self):
        QtWidgets.QApplication.clipboard().setText(str(LOG_DIR))
        self._log(f"Log-Pfad kopiert: {LOG_DIR}")

    def _validate_output_template(self):
        result = validate_output_template(self.output_template_edit.text())
        template = result.value
        self.output_template_edit.setText(template)
        if not result.is_valid:
            QtWidgets.QMessageBox.warning(
                self,
                self._ui_text(
                    "dialogs.template_invalid.title", "Template ungültig"
                ),
                result.message,
            )
            self._log(
                f"Dateinamen-Template ungültig: {result.message}",
                logging.ERROR,
            )
        self.settings.setValue("encode/output_template", template)
        self._log("Dateinamen-Template gespeichert.")

    def _show_help_window(self):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Kurzanleitung")
        layout = QtWidgets.QVBoxLayout(dlg)
        layout.addWidget(HelpPane())
        dlg.resize(400, 300)
        dlg.exec()
        self._log("Hilfefenster geöffnet")

    def _show_guided_wizard(self):
        dlg = GuidedWizard(self)
        dlg.exec()
        self._log("Geführter Start geöffnet")

    def _add_form(
        self,
        layout: QtWidgets.QFormLayout,
        label: str,
        widget: QtWidgets.QWidget,
        help_text: str,
    ):
        widget.setToolTip(help_text)
        widget.setStatusTip(help_text)
        hint = QtWidgets.QLabel(f"<small>{help_text}</small>")
        hint.setWordWrap(True)
        box = QtWidgets.QVBoxLayout()
        box.addWidget(widget)
        box.addWidget(hint)
        wrap = QtWidgets.QWidget()
        wrap.setLayout(box)
        layout.addRow(label, wrap)

    def _wrap_button(
        self, button: QtWidgets.QAbstractButton, help_text: str
    ) -> QtWidgets.QWidget:
        """Return button with help label underneath."""
        button.setToolTip(help_text)
        button.setStatusTip(help_text)
        button.setAccessibleName(button.text())
        button.setAccessibleDescription(help_text)
        lbl = QtWidgets.QLabel(f"<small>{help_text}</small>")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        button.setMaximumHeight(16777215)
        button.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )
        box = QtWidgets.QVBoxLayout()
        box.setContentsMargins(2, 0, 2, 0)
        box.setSpacing(1)
        box.addWidget(button)
        box.addWidget(lbl)
        w = QtWidgets.QWidget()
        w.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum,
        )
        w.setLayout(box)
        return w

    def _action_buttons(self) -> Tuple[QtWidgets.QPushButton, ...]:
        """Return all primary action buttons in one place."""
        return (
            self.btn_add_images,
            self.btn_add_audios,
            self.btn_auto_pair,
            self.btn_clear,
            self.btn_undo,
            self.btn_save,
            self.btn_load,
            self.btn_encode,
            self.btn_stop,
            self.btn_wizard,
            self.btn_out_open,
        )

    def _normalize_action_layout_width(self, available_width: int) -> int:
        if isinstance(available_width, int):
            return available_width
        self._log(
            "Interner Layout-Hinweis: verfügbare Breite ist ungültig, nutze sicheren Standard.",
            logging.WARNING,
        )
        return 0

    def _resolve_action_columns(
        self,
        wrappers: Sequence[QtWidgets.QWidget],
        available_width: int,
    ) -> Tuple[int, int]:
        spacing = max(self.top_buttons_layout.horizontalSpacing(), 0)
        margins = self.top_buttons_layout.contentsMargins()
        usable_width = max(
            available_width - margins.left() - margins.right(),
            240,
        )
        button_font = QtGui.QFontMetrics(self.btn_encode.font())
        dynamic_min_width = max(
            160,
            button_font.horizontalAdvance("Gespeichertes Projekt laden") + 60,
        )
        min_cell_width = max(
            max((w.minimumWidth() for w in wrappers), default=190),
            dynamic_min_width,
        )
        max_columns = 4 if usable_width >= 1100 else 3
        columns = max(
            1,
            min(max_columns, usable_width // max(min_cell_width + spacing, 1)),
        )
        return columns, max_columns

    def _compute_workflow_min_size(self) -> Tuple[int, int]:
        base_font = self._font_size if isinstance(self._font_size, int) else 13
        base_font = max(10, min(36, int(base_font)))
        scale = max(1.0, base_font / 13.0)
        min_width = int(
            max(
                self.WORKFLOW_SECTION_MIN_WIDTH,
                min(460, self.WORKFLOW_SECTION_MIN_WIDTH * scale),
            )
        )
        min_height = int(
            max(
                self.WORKFLOW_SECTION_MIN_HEIGHT,
                min(340, self.WORKFLOW_SECTION_MIN_HEIGHT * scale),
            )
        )
        return min_width, min_height

    def _reflow_action_buttons(self, available_width: int) -> None:
        if not hasattr(self, "top_buttons_layout"):
            return
        wrappers = getattr(self, "_action_button_wrappers", [])
        if not wrappers:
            return
        available_width = self._normalize_action_layout_width(available_width)
        while self.top_buttons_layout.count():
            item = self.top_buttons_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        columns, max_columns = self._resolve_action_columns(
            wrappers,
            available_width,
        )
        for i, wrapper in enumerate(wrappers):
            row = i // columns
            col = i % columns
            self.top_buttons_layout.addWidget(wrapper, row, col)
        for i in range(max_columns):
            stretch = 1 if i < columns else 0
            self.top_buttons_layout.setColumnStretch(i, stretch)

    def _log(self, msg: str, level=logging.INFO):
        if level >= logging.INFO or self.debug_mode:
            self.log_edit.appendPlainText(msg)
            self.dashboard.log(msg)
        logger.log(level, msg)

    def _log_details(self, max_chars: int = 4000) -> str:
        try:
            text = LOG_FILE.read_text(encoding="utf-8", errors="replace")
        except (FileNotFoundError, PermissionError, OSError) as exc:
            logger.warning(
                "ui.log_read_failed",
                extra={"log_file": str(LOG_FILE), "error": str(exc)},
            )
            return (
                f"Logdatei: {LOG_FILE}\n"
                "Log konnte nicht gelesen werden. Nächster Schritt: Rechte prüfen mit "
                f"'ls -l {LOG_FILE}'. Detail: {exc}"
            )
        if len(text) > max_chars:
            text = "... (gekürzt)\n" + text[-max_chars:]
        return f"Logdatei: {LOG_FILE}\n\n{text}"

    def _on_audio_preview_error(self, error, error_string) -> None:
        if error:
            self._log(f"Audio-Vorschau Fehler: {error_string}", logging.ERROR)

    def _play_audio_preview(self, path: str) -> None:
        ok, detail = play_audio_preview(self._audio_player, path)
        if not ok and detail != "Leerpfad":
            self._show_error_dialog(
                "Audio fehlt",
                detail,
                QtWidgets.QMessageBox.Warning,
            )
            return
        if ok:
            self._log(f"Audio-Vorschau gestartet: {detail}")

    def _stop_audio_preview(self) -> None:
        if stop_audio_preview(self._audio_player):
            self._log("Audio-Vorschau gestoppt")

    def _restore_window_state(self) -> None:
        geometry = self.settings.value("ui/window_geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = self.settings.value("ui/window_state")
        if state:
            self.restoreState(state)

    def _show_error_dialog(
        self,
        title: str,
        message: str,
        icon: QtWidgets.QMessageBox.Icon = QtWidgets.QMessageBox.Critical,
    ) -> None:
        box = QtWidgets.QMessageBox(self)
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(message)
        box.setDetailedText(self._log_details())
        box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        box.exec()

    def _normalize_error_message(self, msg: str) -> str:
        replacements = {
            "Fehlendes Audio": "Bitte Audio hinzufügen oder Modus ändern",
            "FFmpeg-Fehler": "FFmpeg installieren oder im Setup reparieren",
        }
        for old, new in replacements.items():
            if old in msg:
                return msg.replace(old, new)
        return msg

    def _debug(self, msg: str):
        self._log(f"DEBUG: {msg}", logging.DEBUG)

    def _get_last_dir(self, key: str, fallback: Path) -> str:
        value = self.settings.value(key, "", str)
        if value:
            stored = Path(value)
            if stored.exists():
                return str(stored)
        project_root = self._get_project_root()
        if project_root:
            return str(project_root)
        return str(fallback)

    def _get_project_start_dir(self) -> str:
        return get_project_start_dir(
            self.settings,
            self.project_dir_edit.text(),
            last_dir_resolver=self._get_last_dir,
        )

    def _get_project_root(self) -> Optional[Path]:
        return get_project_root(self.settings)

    def _set_project_root(self, path: Path) -> None:
        set_project_root(self.settings, path, log_callback=self._log)

    def _set_last_dir(self, key: str, path: Path | str) -> None:
        if not path:
            return
        stored = Path(path).expanduser()
        if stored.is_file():
            stored = stored.parent
        self.settings.setValue(key, str(stored))
        if key == "ui/last_image_dir":
            self.state.last_image_dir = stored
        elif key == "ui/last_audio_dir":
            self.state.last_audio_dir = stored

    def _set_last_project_path(self, path: str) -> None:
        set_last_project_path(self.settings, self.state, path)

    def _choose_project_root(self) -> None:
        start_dir = self._get_last_dir("ui/last_project_root_dir", Path.cwd())
        project_root = choose_project_root_dialog(self, start_dir, UI_TEXTS)
        if project_root is None:
            return
        self._set_project_root(project_root)

    def _make_project_relative(self, path: str) -> str:
        return make_project_relative(path, self._get_project_root())

    def _resolve_project_path(
        self, path: str, project_file: Optional[Path]
    ) -> str:
        return resolve_project_path(
            path, self._get_project_root(), project_file
        )

    def _project_payload(self) -> Dict[str, Any]:
        return build_project_payload(
            self.pairs,
            self._gather_settings() or {},
            self._get_project_root(),
        )

    def _auto_save_project(self, reason: str) -> None:
        if not self.auto_save_project.isChecked():
            return
        auto_path = self.settings.value("ui/auto_save_path", "", str)
        if not auto_path:
            auto_path = str(Path.home() / "videobatch_autosave.json")
            self.settings.setValue("ui/auto_save_path", auto_path)
        try:
            save_project_file(Path(auto_path), self._project_payload())
        except (PermissionError, OSError, TypeError, ValueError) as exc:
            logger.exception(
                "ui.autosave_failed",
                extra={
                    "path": str(auto_path),
                    "reason": reason,
                    "error": str(exc),
                },
            )
            self._log(
                "Auto-Speichern fehlgeschlagen. Ursache: kein Zugriff oder ungültige Daten. "
                "Nächster Schritt: Projekt manuell speichern. "
                f"Befehl: cp '{auto_path}' ./backup_projekt.json (Detail: {exc})",
                logging.ERROR,
            )
            return
        self._log(f"Auto-Speichern ok ({reason}): {auto_path}")

    def _push_history(self):
        snap = []
        for p in self.pairs:
            q = PairItem(p.image_path, p.audio_path)
            q.duration = p.duration
            q.output = p.output
            q.status = p.status
            q.progress = p.progress
            q.valid = p.valid
            q.validation_msg = p.validation_msg
            snap.append(q)
        self._history.append(snap)
        if len(self._history) > 30:
            self._history.pop(0)

    def _update_counts(self):
        img_count = self.image_list.count()
        aud_count = self.audio_list.count()
        selected_images = len(self.image_list.selectedItems())
        selected_audios = len(self.audio_list.selectedItems())
        pair_count = sum(1 for p in self.pairs if p.image_path and p.audio_path)
        err_count = sum(1 for p in self.pairs if p.status == "FEHLER")
        fin_count = sum(1 for p in self.pairs if p.status == "FERTIG")
        status_template = text_with_fallback(
            UI_TEXTS,
            "statusbar.counts",
            "{images} Bilder | {audios} Audios | {pairs} Paare | Auswahl: {selected_images}B/{selected_audios}A",
        )
        self.count_label.setText(
            status_template.format(
                images=img_count,
                audios=aud_count,
                pairs=pair_count,
                selected_images=selected_images,
                selected_audios=selected_audios,
            )
        )
        self.dashboard.set_counts(pair_count, fin_count, err_count)
        self.dashboard.set_selection_counts(selected_images, selected_audios)
        self._update_encode_ready_indicator(pair_count)

    def _update_encode_ready_indicator(self, pair_count: int) -> None:
        if pair_count > 0 and not self.btn_stop.isEnabled():
            if not self._encode_ready_timer.isActive():
                self._encode_ready_timer.start()
                self._encode_ready_on = False
        else:
            if self._encode_ready_timer.isActive():
                self._encode_ready_timer.stop()
            self._encode_ready_on = False
        self._sync_encode_button_state()

    def _toggle_encode_ready_style(self) -> None:
        self._encode_ready_on = not self._encode_ready_on
        self._sync_encode_button_state()

    def _refresh_structure_view(self) -> None:
        if not hasattr(self, "structure_tree"):
            return
        self.structure_tree.clear()

        image_paths = [
            self.image_list.item(i).data(Qt.UserRole)
            for i in range(self.image_list.count())
        ]
        audio_paths = [
            self.audio_list.item(i).data(Qt.UserRole)
            for i in range(self.audio_list.count())
        ]
        image_seen = {path for path in image_paths if path}
        audio_seen = {path for path in audio_paths if path}
        for pair in self.pairs:
            if pair.image_path and pair.image_path not in image_seen:
                image_paths.append(pair.image_path)
                image_seen.add(pair.image_path)
            if pair.audio_path and pair.audio_path not in audio_seen:
                audio_paths.append(pair.audio_path)
                audio_seen.add(pair.audio_path)

        def add_root(title: str, count: int) -> QtWidgets.QTreeWidgetItem:
            root = QtWidgets.QTreeWidgetItem([f"{title} ({count})"])
            root.setData(0, Qt.UserRole, title)
            self.structure_tree.addTopLevelItem(root)
            return root

        def add_path_items(
            root: QtWidgets.QTreeWidgetItem, paths: List[str]
        ) -> None:
            for path in paths:
                if not path:
                    continue
                item = QtWidgets.QTreeWidgetItem([path])
                item.setData(0, Qt.UserRole, path)
                root.addChild(item)

        img_root = add_root("Bilder", len(image_paths))
        add_path_items(img_root, image_paths)

        aud_root = add_root("Audios", len(audio_paths))
        add_path_items(aud_root, audio_paths)

        output_root = add_root("Output", 0)
        output_dir = self.out_dir_edit.text().strip()
        output_files: List[str] = []
        if output_dir:
            out_path = Path(output_dir).expanduser()
            output_dir_item = QtWidgets.QTreeWidgetItem([f"Ordner: {out_path}"])
            output_dir_item.setData(0, Qt.UserRole, str(out_path))
            output_root.addChild(output_dir_item)
            if out_path.exists() and out_path.is_dir():
                try:
                    output_files = [
                        str(p)
                        for p in sorted(out_path.rglob("*"))
                        if p.is_file() and p.suffix.lower() in OUTPUT_EXTENSIONS
                    ]
                except (PermissionError, OSError) as exc:
                    logger.warning(
                        "ui.structure_scan_failed",
                        extra={"path": str(out_path), "error": str(exc)},
                    )
                    error_item = QtWidgets.QTreeWidgetItem(
                        [
                            "Ausgabeordner konnte nicht gelesen werden. "
                            "Bitte Rechte pruefen. "
                            f"Befehl: ls -la '{out_path}'"
                        ]
                    )
                    output_root.addChild(error_item)
            else:
                hint_item = QtWidgets.QTreeWidgetItem(
                    ["Ordner existiert noch nicht."]
                )
                output_root.addChild(hint_item)
        else:
            hint_item = QtWidgets.QTreeWidgetItem(
                ["Kein Ausgabeordner gesetzt."]
            )
            output_root.addChild(hint_item)

        max_outputs = 200
        for path in output_files[:max_outputs]:
            item = QtWidgets.QTreeWidgetItem([path])
            item.setData(0, Qt.UserRole, path)
            output_root.addChild(item)
        if len(output_files) > max_outputs:
            output_root.addChild(
                QtWidgets.QTreeWidgetItem(
                    [f"… weitere {len(output_files) - max_outputs} Dateien"]
                )
            )
        output_root.setText(0, f"Output ({len(output_files)})")

        self.structure_tree.expandAll()
        self._apply_structure_filter()

    def _apply_structure_filter(self) -> None:
        if not hasattr(self, "structure_tree"):
            return
        filter_text = self.structure_filter.currentText()
        search_text = self.structure_search.text().strip().lower()
        for i in range(self.structure_tree.topLevelItemCount()):
            root = self.structure_tree.topLevelItem(i)
            category = root.data(0, Qt.UserRole) or ""
            allow_category = filter_text in ("Alles", category)
            visible_children = 0
            for j in range(root.childCount()):
                child = root.child(j)
                path_text = (
                    child.data(0, Qt.UserRole) or child.text(0)
                ).lower()
                matches = (not search_text) or (search_text in path_text)
                child_visible = allow_category and matches
                child.setHidden(not child_visible)
                if child_visible:
                    visible_children += 1
            root.setHidden(not allow_category or visible_children == 0)

    # ----- file actions -----
    def _select_files_with_preview(
        self,
        title: str,
        start_dir: Path,
        suffixes: Tuple[str, ...],
        mode: str,
    ) -> List[str]:
        dialog = FilePickerDialog(
            self,
            title,
            start_dir=start_dir,
            suffixes=suffixes,
            mode=mode,
            texts=UI_TEXTS,
        )
        if dialog.exec():
            return dialog.selected_files()
        return []

    def _pick_images(self):
        mode = self.mode_combo.currentText()
        start_dir = self._get_last_dir(
            "ui/last_image_dir", default_downloads_dir()
        )
        if mode == "Slideshow":
            d = QtWidgets.QFileDialog.getExistingDirectory(
                self,
                text_with_fallback(
                    UI_TEXTS,
                    "dialog.image_folder.title",
                    "Ordner mit Bildern wählen",
                ),
                start_dir,
            )
            if d:
                self._set_last_dir("ui/last_image_dir", d)
                self._on_images_added([d])
        else:
            files = self._select_files_with_preview(
                "Bilder wählen",
                Path(start_dir),
                IMAGE_EXTENSIONS,
                mode="image",
            )
            if files:
                self._set_last_dir("ui/last_image_dir", Path(files[0]).parent)
                self._on_images_added(files)

    def _pick_audios(self):
        start_dir = self._get_last_dir(
            "ui/last_audio_dir", default_downloads_dir()
        )
        files = self._select_files_with_preview(
            "Audios wählen",
            Path(start_dir),
            AUDIO_EXTENSIONS,
            mode="audio",
        )
        if files:
            self._set_last_dir("ui/last_audio_dir", Path(files[0]).parent)
            self._on_audios_added(files)

    def _pick_image_folder(self):
        start_dir = self._get_last_dir(
            "ui/last_image_dir", default_downloads_dir()
        )
        d = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Bildordner wählen", start_dir
        )
        if not d:
            return
        self._set_last_dir("ui/last_image_dir", d)
        files = self._collect_media_files(
            Path(d),
            IMAGE_EXTENSIONS,
        )
        if not files:
            QtWidgets.QMessageBox.information(
                self,
                "Keine Bilder",
                "Im Ordner wurden keine Bilddateien gefunden.",
            )
            return
        self._on_images_added([str(f) for f in files])

    def _pick_audio_folder(self):
        start_dir = self._get_last_dir(
            "ui/last_audio_dir", default_downloads_dir()
        )
        d = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Audioordner wählen", start_dir
        )
        if not d:
            return
        self._set_last_dir("ui/last_audio_dir", d)
        files = self._collect_media_files(Path(d), AUDIO_EXTENSIONS)
        if not files:
            QtWidgets.QMessageBox.information(
                self,
                "Keine Audios",
                "Im Ordner wurden keine Audiodateien gefunden.",
            )
            return
        self._on_audios_added([str(f) for f in files])

    def _collect_media_files(
        self, folder: Path, suffixes: Tuple[str, ...]
    ) -> List[Path]:
        if not folder.exists() or not folder.is_dir():
            return []
        files = [
            p
            for p in folder.rglob("*")
            if p.is_file() and p.suffix.lower() in suffixes
        ]
        return sorted(files)

    def _on_images_added(self, files: List[str]):
        self._push_history()
        for f in files:
            self.image_list.add_files([f])
            self.model.add_pairs([PairItem(f)])
            self._debug(f"Bild hinzugefügt: {f}")
        self._update_counts()
        self._resize_columns()
        self._refresh_structure_view()
        self._log(f"{len(files)} Bild(er) hinzugefügt")

    def _on_audios_added(self, files: List[str]):
        self._push_history()
        for f in files:
            self.audio_list.add_files([f])
            self._debug(f"Audio hinzugefügt: {f}")
        it = iter(files)
        for p in self.pairs:
            if p.audio_path is None:
                try:
                    p.audio_path = next(it)
                    p.update_duration()
                    p.validate()
                except StopIteration:
                    break
        self.model.layoutChanged.emit()
        self._update_counts()
        self._resize_columns()
        self._refresh_structure_view()
        self._log(f"{len(files)} Audio(s) hinzugefügt")

    def _add_to_favorites(self, path: str):
        for i in range(self.favorite_list.count()):
            if self.favorite_list.item(i).data(Qt.UserRole) == path:
                return
        self.favorite_list.add_files([path])
        self._log(f"Favorit hinzugefügt: {path}")

    def _use_favorite(self, path: str):
        self._on_images_added([path])
        self._log(f"Favorit genutzt: {path}")

    def _auto_pair(self):
        self._push_history()
        imgs = [
            self.image_list.item(i).data(Qt.UserRole)
            for i in range(self.image_list.count())
        ]
        auds = [
            self.audio_list.item(i).data(Qt.UserRole)
            for i in range(self.audio_list.count())
        ]
        self._debug(
            f"Auto-Pair start mit {len(imgs)} Bild(er) und {len(auds)} Audio(s)"
        )
        self.model.clear()
        new = []
        mode = self.mode_combo.currentText()
        if mode == "Mehrere Audios, 1 Bild" and imgs:
            img = imgs[0]
            for aud in auds:
                p = PairItem(img, aud)
                p.update_duration()
                p.validate()
                new.append(p)
        elif mode == "Slideshow":
            if len(imgs) == len(auds):
                pairs = zip(imgs, auds)
            elif len(imgs) == 1:
                pairs = ((imgs[0], a) for a in auds)
            else:
                pairs = zip(imgs, auds)
            for img, aud in pairs:
                p = PairItem(img, aud)
                p.update_duration()
                p.validate()
                new.append(p)
        else:
            for img, aud in zip(imgs, auds):
                p = PairItem(img, aud)
                p.update_duration()
                p.validate()
                new.append(p)
        self.model.add_pairs(new)
        self._debug(
            f"Auto-Pair Ergebnis: {[(p.image_path, p.audio_path) for p in new][:3]} ..."
        )
        self._update_counts()
        self._resize_columns()
        self._log(f"Auto-Pair erstellt {len(new)} Paar(e)")

    def _clear_all(self):
        if (
            QtWidgets.QMessageBox.question(
                self, "Löschen?", "Alle Paare wirklich entfernen?"
            )
            != QtWidgets.QMessageBox.Yes
        ):
            return
        self._push_history()
        self.model.clear()
        self.image_list.clear()
        self.audio_list.clear()
        self.log_edit.clear()
        self.dashboard.mini_log.clear()
        self._update_counts()
        self._refresh_structure_view()
        self._log(
            "Listen sicher geleert (Auswahl, Tabelle, Vorschau und Kurzprotokoll zurückgesetzt)"
        )

    def _undo_last(self):
        if not self._history:
            return
        last = self._history.pop()
        self.model.clear()
        self.model.add_pairs(last)
        self._update_counts()
        self._resize_columns()
        self._refresh_structure_view()
        self._log("Rückgängig ausgeführt")

    # ----- save / load -----
    def _save_project(self):
        start_dir = self._get_project_start_dir()
        start_path = str(Path(start_dir) / "projekt.json")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Projekt speichern", start_path, "JSON (*.json)"
        )
        if not path:
            return
        data = self._project_payload()
        data["settings"] = self._gather_settings(require_valid=False)
        data = {
            "pairs": [
                {
                    "image": p.image_path,
                    "audio": p.audio_path,
                    "output": p.output,
                }
                for p in self.pairs
            ],
            "settings": self._gather_settings(require_valid=False),
        }
        try:
            save_project_file(Path(path), data)
        except (PermissionError, OSError, TypeError, ValueError) as exc:
            logger.exception(
                "ui.project_save_failed",
                extra={"path": path, "error": str(exc)},
            )
            user_msg = (
                "Projekt konnte nicht gespeichert werden. "
                "Ursache: Rechteproblem oder ungültige Daten. "
                "Nächster Schritt: anderen Speicherort wählen. "
                f"Befehl: mkdir -p '{Path(path).parent}'"
            )
            self._show_error_dialog(
                "Fehler beim Speichern",
                f"{user_msg}\n\nTechnik-Detail: {exc}",
            )
            return
        self._set_last_project_path(path)
        self._refresh_structure_view()
        self._log(f"Projekt gespeichert: {path}")

    def _load_project(self):
        start_dir = self._get_project_start_dir()
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Projekt laden", start_dir, "JSON (*.json)"
        )
        if not path:
            return
        try:
            data = load_project_file(Path(path))
        except FileNotFoundError as exc:
            logger.warning(
                "ui.project_load_missing",
                extra={"path": path, "error": str(exc)},
            )
            self._show_error_dialog(
                "Fehler beim Laden",
                "Projektdatei fehlt. Nächster Schritt: Datei erneut auswählen. "
                f"Befehl: ls -l '{path}'\n\nTechnik-Detail: {exc}",
            )
            self._log(f"Fehler beim Laden: {exc}")
            return
        except (
            PermissionError,
            OSError,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            logger.exception(
                "ui.project_load_failed",
                extra={"path": path, "error": str(exc)},
            )
            self._show_error_dialog(
                "Fehler beim Laden",
                "Projektdatei konnte nicht geladen werden. "
                "Ursache: keine Rechte oder defekte JSON-Datei. "
                "Nächster Schritt: Datei prüfen oder Backup laden. "
                f"Befehl: python3 -m json.tool '{path}'\n\nTechnik-Detail: {exc}",
            )
            self._log(f"Fehler beim Laden: {exc}")
            return
        self._set_last_project_path(path)
        self._push_history()
        self.model.clear()
        project_file = Path(path).expanduser()
        new = []
        for d in data.get("pairs", []):
            image_path = self._resolve_project_path(
                d.get("image", ""), project_file
            )
            audio_path = self._resolve_project_path(
                d.get("audio", ""), project_file
            )
            output_path = self._resolve_project_path(
                d.get("output", ""), project_file
            )
            p = PairItem(image_path, audio_path or None)
            p.output = output_path
            p.update_duration()
            p.validate()
            new.append(p)
        self.model.add_pairs(new)
        s = data.get("settings", {})
        self.out_dir_edit.setText(s.get("out_dir", self.out_dir_edit.text()))
        self.crf_spin.setValue(s.get("crf", self.crf_spin.value()))
        self.preset_combo.setCurrentText(
            s.get("preset", self.preset_combo.currentText())
        )
        self.width_spin.setValue(s.get("width", self.width_spin.value()))
        self.height_spin.setValue(s.get("height", self.height_spin.value()))
        self.abitrate_edit.setText(s.get("abitrate", self.abitrate_edit.text()))
        self.output_template_edit.setText(
            s.get("output_template", self.output_template_edit.text())
        )
        self.mode_combo.setCurrentText(
            s.get("mode", self.mode_combo.currentText())
        )
        self.parallel_jobs_spin.setValue(
            s.get("parallel_jobs", self.parallel_jobs_spin.value())
        )
        self._update_counts()
        self._resize_columns()
        self._refresh_structure_view()
        self._log(f"Projekt geladen: {path}")

    # ----- encode -----
    def _gather_settings(
        self, require_valid: bool = True
    ) -> Optional[Dict[str, Any]]:
        bitrate_result = normalize_audio_bitrate(self.abitrate_edit.text())
        abitrate = bitrate_result.value
        self.abitrate_edit.setText(abitrate)
        if bitrate_result.message and bitrate_result.is_valid:
            self._log(bitrate_result.message)
        if require_valid and not bitrate_result.is_valid:
            QtWidgets.QMessageBox.warning(
                self,
                "Ungültige Audiobitrate",
                bitrate_result.message,
            )
            self._log("Abbruch: Audiobitrate ist ungültig.")
            return None

        template_result = validate_output_template(
            self.output_template_edit.text()
        )
        output_template = template_result.value
        self.output_template_edit.setText(output_template)
        if require_valid and not template_result.is_valid:
            QtWidgets.QMessageBox.warning(
                self,
                "Ungültiges Template",
                template_result.message,
            )
            self._log("Abbruch: Dateinamen-Template ist ungültig.")
            return None
        if not template_result.is_valid:
            self._log("Hinweis: Template ungültig, setze Standard.")
        return {
            "out_dir": self.out_dir_edit.text().strip(),
            "crf": self.crf_spin.value(),
            "preset": self.preset_combo.currentText(),
            "width": self.width_spin.value(),
            "height": self.height_spin.value(),
            "abitrate": abitrate,
            "mode": self.mode_combo.currentText(),
            "output_template": output_template,
            "parallel_jobs": self.parallel_jobs_spin.value(),
        }

    def _dir_has_slideshow_images(self, path: Path) -> bool:
        try:
            for entry in path.iterdir():
                if (
                    entry.is_file()
                    and entry.suffix.lower() in SLIDESHOW_IMAGE_EXTENSIONS
                ):
                    return True
        except (PermissionError, OSError) as exc:
            logger.warning(
                "ui.slideshow_dir_scan_failed",
                extra={"path": str(path), "error": str(exc)},
            )
            return False
        return False

    def _flag_row_error(self, row: int, msg: str):
        if 0 <= row < len(self.pairs):
            item = self.pairs[row]
            item.valid = False
            item.status = "FEHLER"
            item.validation_msg = msg
            left = self.model.index(row, 0)
            right = self.model.index(row, self.model.columnCount() - 1)
            self.model.dataChanged.emit(left, right)
        self._log(f"Fehler in Zeile {row + 1}: {msg}")
        self._update_counts()

    def _load_fallback_audio_paths(self) -> List[str]:
        return [
            path
            for path in loads_audio_list(
                self.settings.value("fallback/audios", "", str)
            )
            if Path(path).exists()
        ]

    def _maybe_apply_fallback_media(self) -> int:
        if not self.fallback_enabled.isChecked():
            return 0
        fallback_image = self.settings.value("fallback/image", "", str).strip()
        fallback_audios = self._load_fallback_audio_paths()
        if not fallback_image and not fallback_audios:
            return 0
        replacements = 0
        for index, pair in enumerate(self.pairs):
            image_missing = (
                not pair.image_path or not Path(pair.image_path).exists()
            )
            audio_missing = (
                not pair.audio_path or not Path(pair.audio_path).exists()
            )
            if (
                image_missing
                and fallback_image
                and Path(fallback_image).exists()
            ):
                pair.image_path = fallback_image
                replacements += 1
            if audio_missing and fallback_audios:
                pair.audio_path = fallback_audios[index % len(fallback_audios)]
                replacements += 1
        if replacements:
            self.model.layoutChanged.emit()
            self._log(
                f"Fallback aktiv: {replacements} fehlerhafte Eingaben ersetzt."
            )
        return replacements

    def _manage_fallback_media(self) -> None:
        info = (
            "Lege ein Ersatzbild und bis zu zwei Ersatz-Audios fest.\n"
            "Diese Dateien werden in den App-Datenordner kopiert und bleiben erhalten.\n\n"
            "PL: Ustaw obraz zapasowy i maksymalnie dwa pliki audio zapasowe. "
            "Pliki pozostają zapisane trwale."
        )
        QtWidgets.QMessageBox.information(
            self,
            self._ui_text("dialogs.fallback_media.title", "Fallback-Medien"),
            info,
        )
        image_file, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Fallback-Bild wählen",
            self._get_last_dir("ui/last_image_dir", default_downloads_dir()),
            "Bild/Video (*.jpg *.jpeg *.png *.bmp *.webp *.mp4 *.mov)",
        )
        audio_files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Bis zu zwei Fallback-Audios wählen",
            self._get_last_dir("ui/last_audio_dir", default_downloads_dir()),
            "Audio (*.mp3 *.wav *.flac *.m4a *.aac)",
        )
        persisted_image, persisted_audio = persist_fallback_media(
            APP_DIR / "fallback_media", image_file, audio_files
        )
        self.settings.setValue("fallback/image", persisted_image)
        self.settings.setValue(
            "fallback/audios", dumps_audio_list(persisted_audio)
        )
        self.settings.setValue(
            "fallback/enabled", self.fallback_enabled.isChecked()
        )
        self._log(
            "Fallback-Medien gespeichert: "
            f"Bild={'ja' if persisted_image else 'nein'}, Audio={len(persisted_audio)}"
        )

    def _start_encode(self):
        settings = self._gather_settings()
        if settings is None:
            return
        self._maybe_apply_fallback_media()
        if self.image_list.count() == 0:
            self._suggest_add_images()
            return
        if self.audio_list.count() == 0:
            self._suggest_add_audios()
            return
        if not self.pairs:
            QtWidgets.QMessageBox.information(
                self,
                "Keine Paare",
                "Bitte zuerst Bilder und Audios hinzufügen.",
            )
            self._log("Encoding abgebrochen: keine Paare")
            return
        if any(p.audio_path is None for p in self.pairs):
            self._show_error_dialog(
                "Fehlendes Audio",
                "Bitte Audio hinzufügen oder Modus ändern.",
                QtWidgets.QMessageBox.Warning,
            )
            QtWidgets.QMessageBox.warning(
                self, "Fehlende Audios", "Nicht alle Bilder haben ein Audio."
            )
            self._log(
                "Encoding abgebrochen: nicht alle Bilder haben ein Audio."
            )
            return
        mode = settings.get("mode", "Standard")
        if mode == "Mehrere Audios, 1 Bild":
            if self.image_list.count() == 0:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Bild fehlt",
                    "Für diesen Modus wird mindestens ein Bild benötigt.",
                )
                self._log(
                    "Encoding abgebrochen: kein Bild für 'Mehrere Audios, 1 Bild'."
                )
                return
        if mode == "Slideshow":
            invalid_rows = False
            for idx, p in enumerate(self.pairs):
                img_path = Path(p.image_path) if p.image_path else None
                if not img_path or not img_path.is_dir():
                    self._flag_row_error(
                        idx, "Slideshow benötigt einen Ordner mit Bildern."
                    )
                    invalid_rows = True
                    continue
                if not self._dir_has_slideshow_images(img_path):
                    self._flag_row_error(
                        idx, "Im Bildordner sind keine Bilddateien vorhanden."
                    )
                    invalid_rows = True
            if invalid_rows:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Slideshow-Ordner prüfen",
                    "Bitte pro Zeile einen Bildordner mit mindestens einem Bild wählen.",
                )
                return
        for p in self.pairs:
            p.validate()
        invalid = [(i, p) for i, p in enumerate(self.pairs) if not p.valid]
        if invalid:
            row, first_item = invalid[0]
            idx = self.model.index(row, 0)
            first_row, first_item = invalid[0]
            idx = self.model.index(first_row, 0)
            sel = self.table.selectionModel()
            if sel is not None:
                sel.select(
                    idx,
                    QtCore.QItemSelectionModel.ClearAndSelect
                    | QtCore.QItemSelectionModel.Rows,
                )
                self.table.setCurrentIndex(idx)
            self.table.scrollTo(
                idx, QtWidgets.QAbstractItemView.PositionAtCenter
            )
            self.table.setFocus()
            self._show_error_dialog(
                "Validierungsfehler", first_item.validation_msg
            )
            for row, item in invalid:
                self._flag_row_error(row, item.validation_msg)
            self._show_error_dialog(
                "Validierungsfehler", first_item.validation_msg
            )
            for row, item in invalid:
                self._flag_row_error(row, item.validation_msg)
            QtWidgets.QMessageBox.critical(
                self, "Validierungsfehler", first_item.validation_msg
            )
            return
        out_dir_value = settings.get("out_dir", "").strip()
        if not out_dir_value:
            QtWidgets.QMessageBox.warning(
                self,
                "Ausgabeordner fehlt",
                "Bitte einen Ausgabeordner festlegen.",
            )
            self._log("Encoding abgebrochen: Ausgabeordner fehlt.")
            return
        out_dir = Path(out_dir_value)
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            test_file = out_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError) as exc:
            logger.exception(
                "ui.output_dir_write_test_failed",
                extra={"path": str(out_dir), "error": str(exc)},
            )
            user_msg = (
                "Im Ausgabeordner kann nicht geschrieben werden. "
                "Ursache: keine Rechte oder Laufwerk gesperrt. "
                "Nächster Schritt: anderen Ordner wählen oder Rechte prüfen. "
                f"Befehl: touch '{out_dir}/.write_test'"
            )
            self._show_error_dialog(
                "Ordnerproblem",
                f"{user_msg}\n\nTechnik-Detail: {exc}",
            )
            return
        self.btn_encode.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_total.setValue(0)
        self.dashboard.set_progress(0)
        self._log("Starte Encoding …")
        self.worker = EncodeWorker(
            self.pairs,
            settings,
            self.copy_only,
            plugin_manager=self.plugin_manager,
        )
        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.row_progress.connect(self._on_row_progress)
        self.worker.overall_progress.connect(self._on_overall_progress)
        self.worker.row_error.connect(self._on_row_error)
        self.worker.log.connect(self._log)
        self.worker.finished.connect(self._encode_finished)
        self.thread.start()

    def _suggest_add_images(self):
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle(
            self._ui_text("dialogs.missing_images.title", "Bilder fehlen")
        )
        msg.setText(
            self._ui_text(
                "dialogs.missing_images.body", "Bitte zuerst Bilder auswählen."
            )
        )
        msg.setInformativeText(
            self._ui_text(
                "dialogs.missing_images.info",
                "Tipp: Du kannst einzelne Dateien oder einen Ordner wählen.",
            )
        )
        btn_files = msg.addButton(
            self._ui_text(
                "dialogs.missing_images.choose_files", "Bilder wählen"
            ),
            QtWidgets.QMessageBox.AcceptRole,
        )
        btn_folder = msg.addButton(
            self._ui_text(
                "dialogs.missing_images.choose_folder", "Bildordner wählen"
            ),
            QtWidgets.QMessageBox.ActionRole,
        )
        msg.addButton(
            self._ui_text("ui.buttons.cancel", "Abbrechen"),
            QtWidgets.QMessageBox.RejectRole,
        )
        msg.exec()
        if msg.clickedButton() == btn_files:
            self._pick_images()
        elif msg.clickedButton() == btn_folder:
            self._pick_image_folder()

    def _suggest_add_audios(self):
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle(
            self._ui_text("dialogs.missing_audios.title", "Audios fehlen")
        )
        msg.setText(
            self._ui_text(
                "dialogs.missing_audios.body", "Bitte Audiodateien auswählen."
            )
        )
        msg.setInformativeText(
            self._ui_text(
                "dialogs.missing_audios.info",
                "Tipp: Ein Audio pro Bild, oder nutze den Modus 'Mehrere Audios, 1 Bild'.",
            )
        )
        btn_files = msg.addButton(
            self._ui_text(
                "dialogs.missing_audios.choose_files", "Audios wählen"
            ),
            QtWidgets.QMessageBox.AcceptRole,
        )
        btn_folder = msg.addButton(
            self._ui_text(
                "dialogs.missing_audios.choose_folder", "Audioordner wählen"
            ),
            QtWidgets.QMessageBox.ActionRole,
        )
        msg.addButton(
            self._ui_text("ui.buttons.cancel", "Abbrechen"),
            QtWidgets.QMessageBox.RejectRole,
        )
        msg.exec()
        if msg.clickedButton() == btn_files:
            self._pick_audios()
        elif msg.clickedButton() == btn_folder:
            self._pick_audio_folder()

    def _stop_encode(self):
        if self.worker:
            self.worker.stop()
        self.btn_stop.setEnabled(False)
        self._log("Encoding gestoppt")

    def _on_row_progress(self, row: int, perc: float):
        if 0 <= row < len(self.pairs):
            self.pairs[row].progress = perc
            idx = self.model.index(row, 6)
            self.model.dataChanged.emit(idx, idx)

    def _on_overall_progress(self, perc: float):
        v = int(perc)
        processed = sum(
            1
            for pair in self.pairs
            if pair.status in {"FERTIG", "FEHLER", "ABGEBROCHEN"}
        )
        total = max(1, len(self.pairs))
        self.progress_total.setFormat(
            f"%p% gesamt ({processed}/{total} erledigt)"
        )
        self.progress_total.setValue(v)
        self.dashboard.set_progress(v)

    def _on_row_error(self, row: int, msg: str):
        msg = self._normalize_error_message(msg)
        self._log(f"Fehler in Zeile {row + 1}: {msg}")
        if 0 <= row < len(self.pairs):
            self.pairs[row].status = "FEHLER"
            idx = self.model.index(row, 7)
            self.model.dataChanged.emit(idx, idx)
            self.table.scrollTo(
                idx, QtWidgets.QAbstractItemView.PositionAtCenter
            )
        self._show_error_dialog("Fehler in Zeile", msg)
        self._update_counts()
        self._flag_row_error(row, msg)

    def _encode_finished(self):
        self.btn_encode.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_total.setValue(100)
        self.dashboard.set_progress(100)
        self._log("Alle Jobs abgeschlossen.")
        if self.thread:
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.worker = None
        self._update_counts()
        summary_dir = self._archive_generation_run()
        if summary_dir is not None:
            self._log(f"Generierungsablage erstellt: {summary_dir}")
        QtWidgets.QApplication.beep()
        self.raise_()
        self.activateWindow()
        done_count = sum(1 for pair in self.pairs if pair.status == "FERTIG")
        QtWidgets.QMessageBox.information(
            self,
            "Fertig",
            (
                f"Videogenerierung abgeschlossen: {done_count} Datei(en).\n"
                "Der Zielordner wird jetzt geöffnet."
            ),
        )
        self._open_out_dir()
        if self.clear_after.isChecked():
            self._clear_all()

    # ----- misc -----
    def _archive_generation_run(self) -> Optional[Path]:
        out_dir_value = self.out_dir_edit.text().strip()
        if not out_dir_value:
            return None
        out_dir = Path(out_dir_value)
        if not out_dir.exists():
            return None
        finished = [
            pair
            for pair in self.pairs
            if pair.status == "FERTIG"
            and pair.output
            and Path(pair.output).exists()
        ]
        if not finished:
            return None
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        bundle_dir = out_dir / f"videogenerierung_{timestamp}"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        inputs_dir = bundle_dir / "eingaben"
        outputs_dir = bundle_dir / "ausgaben"
        inputs_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)

        copied_inputs = 0
        for pair in finished:
            for path_str in (pair.image_path, pair.audio_path):
                if not path_str:
                    continue
                src = Path(path_str)
                if not src.exists():
                    continue
                safe_move(src, inputs_dir, copy_only=True)
                copied_inputs += 1
        copied_outputs = 0
        for pair in finished:
            if not pair.output:
                continue
            src = Path(pair.output)
            if not src.exists():
                continue
            safe_move(src, outputs_dir, copy_only=True)
            copied_outputs += 1

        self._log(
            "Ablage gesichert: "
            f"{copied_inputs} Eingabedatei(en), {copied_outputs} Ausgabedatei(en)."
        )
        return bundle_dir

    def _toggle_copy_mode(self, checked: bool):
        self.copy_only = checked
        self._log(
            f"Archivmodus: Dateien werden {'kopiert' if checked else 'verschoben'}."
        )

    def _toggle_help(self, checked: bool):
        self.help_box.setVisible(checked)
        self.settings.setValue("ui/show_help", checked)

    def _toggle_log(self, checked: bool):
        self.log_box.setVisible(checked)
        self.settings.setValue("ui/show_log", checked)

    def _toggle_sidebar(self, checked: bool):
        self.sidebar.setVisible(checked)
        self.settings.setValue("ui/show_sidebar", checked)

    def _toggle_debug(self, checked: bool):
        self._apply_log_level("DEBUG" if checked else "INFO")
        self._log(f"Debug-Log {'aktiviert' if checked else 'deaktiviert'}")

    def _update_log_level(self, level: str) -> None:
        self._apply_log_level(level)
        self._log(f"Protokoll-Stufe gesetzt: {self.log_level}")

    def _toggle_auto_open_output(self, checked: bool):
        self.settings.setValue("ui/auto_open_output", checked)
        self._log(
            "Ausgabeordner wird nach Fertigstellung geöffnet."
            if checked
            else "Ausgabeordner wird nach Fertigstellung nicht geöffnet."
        )

    def _toggle_auto_save_project(self, checked: bool):
        self.settings.setValue("ui/auto_save_project", checked)
        self._log(
            "Auto-Speichern für Start/Schließen aktiviert."
            if checked
            else "Auto-Speichern für Start/Schließen deaktiviert."
        )

    def _update_default_mode(self, mode: str) -> None:
        self.settings.setValue("encode/mode", mode)
        self._log(f"Standard-Modus gesetzt: {mode}")

    def _update_parallel_jobs(self, value: int) -> None:
        self.settings.setValue("encode/parallel_jobs", value)
        self._log(f"Parallelität gesetzt: {value} Job(s)")

    def _update_language(self, language: str) -> None:
        self.settings.setValue("ui/language", language)
        if "Polski" in language:
            self._log(
                "Informacja (PL): Wsparcie tłumaczenia jest przygotowane."
            )
        self._log(f"Sprache vorbereitet: {language}")

    def _update_spacing_profile(self, profile: str) -> None:
        self.settings.setValue("ui/spacing_profile", profile)
        self._apply_spacing_profile(profile)
        self._log(f"Abstandsprofil gesetzt: {profile}")

    def _apply_spacing_profile(self, profile: str) -> None:
        values = resolve_spacing_profile(profile)
        if hasattr(self, "top_buttons_layout"):
            self.top_buttons_layout.setSpacing(values.grid)
            self.top_buttons_layout.setContentsMargins(
                values.margins,
                values.margins,
                values.margins,
                values.margins,
            )
        if hasattr(self, "central_layout"):
            self.central_layout.setSpacing(values.main)
        action_width = self.btn_box.width() if hasattr(self, "btn_box") else 0
        self._reflow_action_buttons(action_width)

    def _update_interface_profile(self, profile: str) -> None:
        self.settings.setValue("ui/interface_profile", profile)
        self._apply_interface_profile(profile)
        self._log(
            f"Interface-Profil gesetzt: {profile}. "
            "Tipp: Seniorenfreundlich ist für sehschwache Nutzer optimiert."
        )

    def _toggle_large_controls(self, checked: bool):
        self.large_controls = checked
        self.settings.setValue("ui/large_controls", checked)
        self._apply_interface_profile(self.interface_combo.currentText())
        self._log(
            f"Große Bedienelemente {'aktiviert' if checked else 'deaktiviert'}"
        )

    def _apply_interface_profile(self, profile: str):
        ui_profile = resolve_interface_profile(profile, self.large_controls)
        font_size = self._font_size + ui_profile.log_font_delta
        height = ui_profile.control_height
        for btn in self._action_buttons():
            btn.setMinimumHeight(height)
            btn.setMinimumWidth(ui_profile.compact_button_min_width)
            btn.setFont(QtGui.QFont("DejaVu Sans", font_size))
        wrapper_min_width = max(ui_profile.compact_button_min_width + 28, 190)
        for wrapper in getattr(self, "_action_button_wrappers", []):
            wrapper.setMinimumWidth(wrapper_min_width)
        action_width = self.btn_box.width() if hasattr(self, "btn_box") else 0
        self._reflow_action_buttons(action_width)
        self.table.verticalHeader().setDefaultSectionSize(
            ui_profile.table_row_height
        )
        self.log_edit.setFont(QtGui.QFont("DejaVu Sans", font_size))
        self._update_workflow_section_constraints()

    def _update_workflow_section_constraints(self) -> None:
        if not hasattr(self, "_workflow_sections"):
            return
        min_width, min_height = self._compute_workflow_min_size()
        for section in self._workflow_sections:
            section.setMinimumSize(min_width, min_height)
        logger.debug(
            "Layout-Skalierung aktualisiert: font=%s min=%sx%s",
            self._font_size,
            min_width,
            min_height,
        )

    def _global_exception(self, etype, value, tb):
        import traceback

        msg = "".join(traceback.format_exception(etype, value, tb))
        self._log(msg, logging.ERROR)
        short = (
            msg
            if len(msg) < 1000
            else msg[:1000] + "\n...\nSiehe Logdatei für Details."
        )
        self._show_error_dialog("Unerwarteter Fehler", short)

    def _resize_columns(self):
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._resize_columns()
        action_width = self.btn_box.width() if hasattr(self, "btn_box") else 0
        self._reflow_action_buttons(action_width)
        QtCore.QTimer.singleShot(0, self._rebalance_workflow_layout)

    def _table_menu(self, pos: QtCore.QPoint):
        index = self.table.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        menu = QtWidgets.QMenu(self)
        act_open = menu.addAction("Im Ordner zeigen")
        act_copy = menu.addAction("Pfad kopieren")
        act_remove = menu.addAction("Zeile löschen")
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == act_open:
            p = self.pairs[row]
            path = p.output or p.image_path or p.audio_path
            if path:
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
                self._log(f"Ordner geöffnet: {path}")
        elif action == act_copy:
            p = self.pairs[row]
            path = p.output or p.image_path or p.audio_path
            if path:
                QtWidgets.QApplication.clipboard().setText(str(path))
                self.statusBar().showMessage(
                    self._ui_text("messages.path_copied", "Pfad kopiert"),
                    2000,
                )
                self._log(f"Pfad kopiert: {path}")
        elif action == act_remove:
            self._push_history()
            self.model.remove_rows([row])
            self._update_counts()
            self._resize_columns()
            self._log(f"Zeile {row + 1} gelöscht")

    def _show_statusbar_path(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return
        if index.column() in (2, 3, 5):
            self.statusBar().showMessage(
                self.model.data(index, Qt.DisplayRole), 5000
            )

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.settings.setValue("ui/geometry", self.saveGeometry())
        self.settings.setValue("ui/window_state", self.saveState())
        self.settings.setValue("ui/clear_after", self.clear_after.isChecked())
        self.settings.setValue(
            "ui/auto_open_output", self.auto_open_output.isChecked()
        )
        self.settings.setValue(
            "ui/auto_save_project", self.auto_save_project.isChecked()
        )
        self.settings.setValue(
            "ui/auto_open_output", self.auto_open_output.isChecked()
        )
        self.settings.setValue(
            "ui/auto_save_project", self.auto_save_project.isChecked()
        )
        s = self._gather_settings(require_valid=False)
        self.settings.setValue("ui/large_controls", self.large_controls)
        self.settings.setValue(
            "project/default_dir", self.project_dir_edit.text().strip()
        )
        self.settings.setValue("log/level", self.log_level)
        self.settings.setValue("ui/language", self.language_combo.currentText())
        self.settings.setValue(
            "fallback/enabled", self.fallback_enabled.isChecked()
        )
        s = self._gather_settings(require_valid=False)
        if s:
            self.settings.setValue("encode/out_dir", s["out_dir"])
            self.settings.setValue("encode/crf", s["crf"])
            self.settings.setValue("encode/preset", s["preset"])
            self.settings.setValue("encode/width", s["width"])
            self.settings.setValue("encode/height", s["height"])
            self.settings.setValue("encode/abitrate", s["abitrate"])
            self.settings.setValue("encode/mode", s["mode"])
            self.settings.setValue(
                "encode/output_template", s["output_template"]
            )
            self.settings.setValue("encode/parallel_jobs", s["parallel_jobs"])
        if self.auto_save_project.isChecked():
            self._auto_save_project("Schließen")
        self._stop_audio_preview()
        super().closeEvent(event)


# ---- Public
def run_gui():
    global THEMES, UI_TEXTS
    THEMES = load_themes(logger)
    UI_TEXTS = load_ui_texts(logger)
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    if QtWidgets.QApplication.instance() is app:
        sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
