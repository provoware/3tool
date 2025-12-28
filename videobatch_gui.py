# =========================================
# QUICKSTART
# Direktstart (wenn alles installiert):  python3 videobatch_gui.py
# Empfohlen (Auto-Setup):                python3 videobatch_launcher.py
# Edit mit micro:                        micro videobatch_gui.py
# =========================================

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PySide6 import QtCore, QtGui, QtWidgets, QtMultimedia
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHeaderView

from core.utils import build_out_name, human_time, probe_duration

# ---------- Paths ----------
APP_DIR = Path.home() / ".videobatchtool"
CONFIG_DIR = APP_DIR / "config"
LOG_DIR = APP_DIR / "logs"
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
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("VideoBatchTool")

# ---------- Themes ----------
# Drei augenschonende Darstellungsstile
FOCUS_STYLE = (
    "QWidget:focus{outline:2px solid #ffbf00;outline-offset:1px;} "
    "QLineEdit:focus,QComboBox:focus,QSpinBox:focus,"
    "QAbstractItemView:focus,QPushButton:focus,QTabBar::tab:focus{"
    "outline:2px solid #ffbf00;outline-offset:1px;}"
)
THEMES = {
    "Modern": (
        "QWidget{background-color:#f6f7fb;color:#1e1e1e;} "
        "QPushButton{background-color:#e6e8f0;color:#1e1e1e;border-radius:4px;} "
        "QLineEdit,QSpinBox,QComboBox,QPlainTextEdit{background-color:#ffffff;color:#1e1e1e;} "
        "QWidget:focus{outline:2px solid #1a73e8;}"
    ),
    "Hell": (
        "QWidget{background-color:#ffffff;color:#202020;} "
        "QPushButton{background-color:#e0e0e0;color:#202020;}"
        + FOCUS_STYLE
    ),
    "Dunkel": (
        "QWidget{background-color:#2b2b2b;color:#e0e0e0;} "
        "QPushButton{background-color:#444;color:#e0e0e0;}"
        + FOCUS_STYLE
    ),
    "Sepia": (
        "QWidget{background-color:#f4ecd8;color:#5b4636;} "
        "QPushButton{background-color:#d6c3a0;color:#5b4636;}"
        + FOCUS_STYLE
    ),
    "Hochkontrast Hell": (
        "QWidget{background-color:#ffffff;color:#000000;} "
        "QPushButton{background-color:#000000;color:#ffffff;border:2px solid #000000;}"
        "QLineEdit,QComboBox,QSpinBox,QPlainTextEdit,QTextBrowser{"
        "background-color:#ffffff;color:#000000;border:2px solid #000000;}"
        "QHeaderView::section{background-color:#000000;color:#ffffff;}"
        + FOCUS_STYLE
    ),
    "Hochkontrast Dunkel": (
        "QWidget{background-color:#000000;color:#ffffff;} "
        "QPushButton{background-color:#ffffff;color:#000000;border:2px solid #ffffff;}"
        "QLineEdit,QComboBox,QSpinBox,QPlainTextEdit,QTextBrowser{"
        "background-color:#000000;color:#ffffff;border:2px solid #ffffff;}"
        "QHeaderView::section{background-color:#ffffff;color:#000000;}"
        + FOCUS_STYLE
        "QPushButton{background-color:#e0e0e0;color:#202020;} "
        "QWidget:focus{outline:2px solid #1a73e8;}"
    ),
    "Dunkel": (
        "QWidget{background-color:#2b2b2b;color:#e0e0e0;} "
        "QPushButton{background-color:#444;color:#e0e0e0;} "
        "QLineEdit,QSpinBox,QComboBox,QPlainTextEdit{background-color:#3a3a3a;color:#f0f0f0;} "
        "QWidget:focus{outline:2px solid #90caf9;}"
    ),
    "Sepia": (
        "QWidget{background-color:#f4ecd8;color:#5b4636;} "
        "QPushButton{background-color:#d6c3a0;color:#5b4636;} "
        "QWidget:focus{outline:2px solid #8d6e63;}"
    ),
    "Hochkontrast Hell": (
        "QWidget{background-color:#ffffff;color:#000000;} "
        "QPushButton{background-color:#000000;color:#ffffff;border:2px solid #000000;} "
        "QLineEdit,QSpinBox,QComboBox,QPlainTextEdit{background-color:#ffffff;color:#000000;border:2px solid #000000;} "
        "QWidget:focus{outline:3px solid #ffbf00;}"
    ),
    "Hochkontrast Dunkel": (
        "QWidget{background-color:#000000;color:#ffffff;} "
        "QPushButton{background-color:#ffffff;color:#000000;border:2px solid #ffffff;} "
        "QLineEdit,QSpinBox,QComboBox,QPlainTextEdit{background-color:#000000;color:#ffffff;border:2px solid #ffffff;} "
        "QWidget:focus{outline:3px solid #ffbf00;}"
    ),
}

# ---------- Helpers ----------
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".mp4", ".mkv", ".avi", ".mov")
AUDIO_EXTENSIONS = (".mp3", ".wav", ".flac", ".m4a", ".aac")
SLIDESHOW_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
OUTPUT_EXTENSIONS = (".mp4", ".mkv", ".avi", ".mov")


def which(p: str):
    return shutil.which(p)


def check_ffmpeg():
    return which("ffmpeg") and which("ffprobe")


def get_used_dir() -> Path:
    return Path.home() / "benutzte_dateien"


def default_output_dir() -> Path:
    return Path.home() / "Videos" / "VideoBatchTool_Out"


def safe_move(src: Path, dst_dir: Path, copy_only: bool = False) -> Path:
    dst_dir.mkdir(parents=True, exist_ok=True)
    tgt = dst_dir / src.name
    if tgt.exists():
        stem, suf = src.stem, src.suffix
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        tgt = dst_dir / f"{stem}_{timestamp}{suf}"
    try:
        if copy_only:
            shutil.copy2(src, tgt)
        else:
            shutil.move(src, tgt)
    except Exception:
        shutil.copy2(src, tgt)
        if not copy_only:
            try:
                src.unlink()
            except Exception as e:
                print("Fehler beim Löschen:", e, file=sys.stderr)
    return tgt

def make_thumb(path: str, size: Tuple[int,int]=(160,90)) -> QtGui.QPixmap:
    try:
        from PIL import Image
        img = Image.open(path)
        img.thumbnail(size)
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        data = img.tobytes("raw", "RGBA")
        qimg = QtGui.QImage(data, img.size[0], img.size[1], QtGui.QImage.Format_RGBA8888)
        return QtGui.QPixmap.fromImage(qimg)
    except Exception:
        pix = QtGui.QPixmap(size[0], size[1])
        pix.fill(Qt.gray)
        return pix


# ---------- Datenmodell ----------
COLUMNS = ["#", "Thumb", "Bild", "Audio", "Dauer", "Ausgabe", "Fortschritt", "Status"]

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

    def update_duration(self):
        if self.audio_path: self.duration = probe_duration(self.audio_path)
    def load_thumb(self):
        if self.thumb is None and self.image_path: self.thumb = make_thumb(self.image_path)
    def validate(self):
        image_path = (self.image_path or "").strip()
        audio_path = (self.audio_path or "").strip() if self.audio_path else ""
        if not image_path or not audio_path:
            self.valid=False; self.validation_msg="Bild oder Audio fehlt"; return
        ip, ap = Path(image_path), Path(audio_path)
        if not ip.exists():
            self.valid=False; self.validation_msg="Bildpfad nicht gefunden"; return
        if not ap.exists():
            self.valid=False; self.validation_msg="Audiopfad nicht gefunden"; return
        if ip.is_dir():
            if not os.access(ip, os.R_OK | os.X_OK):
                self.valid=False; self.validation_msg="Bildordner ist nicht lesbar (keine Rechte)"; return
        else:
            if not os.access(ip, os.R_OK):
                self.valid=False; self.validation_msg="Bilddatei ist nicht lesbar (keine Rechte)"; return
            if ip.suffix.lower() not in IMAGE_EXTENSIONS:
                self.valid=False; self.validation_msg="Ungültiges Bild- oder Videoformat"; return
        if not os.access(ap, os.R_OK):
            self.valid=False; self.validation_msg="Audiodatei ist nicht lesbar (keine Rechte)"; return
        if ap.suffix.lower() not in AUDIO_EXTENSIONS:
            self.valid=False; self.validation_msg="Ungültiges Audioformat"; return
        self.valid=True; self.validation_msg=""

class PairTableModel(QAbstractTableModel):
    def __init__(self, pairs: List[PairItem]):
        super().__init__(); self.pairs = pairs
    def rowCount(self, parent=QModelIndex()): return len(self.pairs)
    def columnCount(self, parent=QModelIndex()): return len(COLUMNS)
    def headerData(self, s, o, role=Qt.DisplayRole):
        if role != Qt.DisplayRole: return None
        return COLUMNS[s] if o == Qt.Horizontal else str(s+1)
    def data(self, idx, role=Qt.DisplayRole):
        if not idx.isValid(): return None
        item = self.pairs[idx.row()]; col = idx.column()
        if role == Qt.DisplayRole:
            if col==0: return str(idx.row()+1)
            if col==2: return item.image_path
            if col==3: return item.audio_path or "—"
            if col==4: return human_time(item.duration) if item.duration else "?"
            if col==5: return item.output or "—"
            if col==6: return f"{int(item.progress)}%"
            if col==7: return item.status
        if role == Qt.DecorationRole and col==1:
            item.load_thumb(); return item.thumb
        if role == Qt.ToolTipRole:
            if col in (2,3,5): return {2:item.image_path,3:item.audio_path or "",5:item.output or ""}[col]
            if not item.valid: return item.validation_msg
        if role == Qt.ForegroundRole and not item.valid:
            return QtGui.QBrush(Qt.red)
        return None
    def flags(self, idx):
        if not idx.isValid(): return Qt.NoItemFlags
        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if idx.column() in (2,3,5): f |= Qt.ItemIsEditable
        return f
    def setData(self, idx, value, role=Qt.EditRole):
        if role != Qt.EditRole or not idx.isValid(): return False
        item = self.pairs[idx.row()]; col = idx.column()
        if col==2: item.image_path=value; item.thumb=None
        elif col==3: item.audio_path=value; item.update_duration()
        elif col==5: item.output=value
        else: return False
        item.validate(); self.dataChanged.emit(idx, idx); return True
    def add_pairs(self, new_pairs: List[PairItem]):
        self.beginInsertRows(QModelIndex(), len(self.pairs), len(self.pairs)+len(new_pairs)-1)
        self.pairs.extend(new_pairs); self.endInsertRows()
    def remove_rows(self, rows: List[int]):
        for r in sorted(rows, reverse=True):
            if 0 <= r < len(self.pairs):
                self.beginRemoveRows(QModelIndex(), r, r)
                self.pairs.pop(r)
                self.endRemoveRows()
    def clear(self):
        self.beginResetModel(); self.pairs.clear(); self.endResetModel()

# ---------- Worker ----------
class EncodeWorker(QtCore.QObject):
    row_progress     = Signal(int, float)
    overall_progress = Signal(float)
    row_error        = Signal(int, str)
    log              = Signal(str)
    finished         = Signal()

    def __init__(self, pairs: List[PairItem], settings: Dict[str, Any], copy_only: bool):
        super().__init__()
        self.pairs = pairs; self.settings = settings; self.copy_only = copy_only; self._stop=False
    def stop(self): self._stop=True
    def _escape_ffmpeg_path(self, path: Path) -> str:
        return path.as_posix().replace("'", r"\'")
    def run(self):
        total = len(self.pairs)
        for i, item in enumerate(self.pairs):
            list_path: Optional[str] = None
            if self._stop: self.log.emit("Abbruch durch Benutzer."); break
            item.validate()
            if not item.valid:
                item.status="FEHLER"; self.row_error.emit(i,item.validation_msg); continue
            try:
                item.status="ENCODIERE"; item.progress=0.0; self.row_progress.emit(i,0.0)
                out_dir = Path(self.settings["out_dir"]).resolve(); out_dir.mkdir(parents=True, exist_ok=True)
                item.output = build_out_name(item.audio_path, out_dir)
                w,h = self.settings["width"], self.settings["height"]
                crf = self.settings["crf"]; preset=self.settings["preset"]; ab=self.settings["abitrate"]
                duration = item.duration or 1
                mode = self.settings.get("mode","Standard")
                if mode == "Video + Audio":
                    vdur = probe_duration(item.image_path)
                    extra = max(0.0, duration - vdur)
                    cmd = ["ffmpeg","-y","-i",item.image_path,"-i",item.audio_path]
                    if extra>0:
                        cmd += ["-vf",f"tpad=stop_mode=clone:stop_duration={extra}","-c:v","libx264"]
                    else:
                        cmd += ["-c:v","copy"]
                    cmd += ["-c:a","aac","-b:a",ab,
                            "-shortest","-preset",preset,"-crf",str(crf),item.output]
                elif mode == "Slideshow":
                    img_dir = Path(item.image_path)
                    imgs = []
                    for ext in ("*.jpg","*.jpeg","*.png","*.bmp","*.webp"):
                        imgs.extend(sorted(img_dir.glob(ext)))
                    if not imgs:
                        raise Exception("Keine Bilder für Slideshow")
                    per = duration/len(imgs) if duration else 2
                    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt') as f:
                        for im in imgs:
                            escaped_path = self._escape_ffmpeg_path(im)
                            f.write(f"file '{escaped_path}'\n")
                            f.write(f"duration {per}\n")
                        escaped_last = self._escape_ffmpeg_path(imgs[-1])
                        f.write(f"file '{escaped_last}'\n")
                        list_path = f.name
                    cmd = ["ffmpeg","-y","-f","concat","-safe","0","-i",list_path,
                           "-i",item.audio_path,
                           "-c:v","libx264",
                           "-vf",f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
                           "-c:a","aac","-b:a",ab,
                           "-shortest","-preset",preset,"-crf",str(crf),item.output]
                else:
                    cmd = ["ffmpeg","-y","-loop","1","-i",item.image_path,"-i",item.audio_path,
                           "-c:v","libx264","-tune","stillimage",
                           "-vf",f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
                           "-c:a","aac","-b:a",ab,"-shortest","-preset",preset,"-crf",str(crf),item.output]
                proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
                for line in proc.stderr:
                    if self._stop: proc.kill(); break
                    if "time=" in line:
                        try:
                            t=line.split("time=")[1].split(" ")[0]
                            h_,m_,s_=t.split(":")
                            elapsed=float(h_)*3600+float(m_)*60+float(s_)
                            perc=min(100.0, elapsed/duration*100.0)
                            item.progress=perc; self.row_progress.emit(i,perc)
                        except Exception as e:
                            print("Fehler beim Lesen des Fortschritts:", e, file=sys.stderr)
                proc.wait()
                if proc.returncode!=0:
                    item.status="FEHLER"; self.row_error.emit(i,"FFmpeg-Fehler")
                    self.log.emit(f"FFmpeg-Fehler bei {item.output}")
                else:
                    item.status="FERTIG"; item.progress=100.0
                    self.row_progress.emit(i,100.0); self.log.emit(f"Fertig: {item.output}")
            except Exception as e:
                item.status="FEHLER"; self.row_error.emit(i,str(e))
                file_hint = item.output or item.image_path or item.audio_path or "unbekannte Datei"
                self.log.emit(f"Fehler bei {file_hint}: {e}")
            finally:
                if list_path:
                    try:
                        Path(list_path).unlink(missing_ok=True)
                    except Exception as cleanup_error:
                        self.log.emit(
                            f"Konnte temporaere Liste nicht loeschen: {list_path} ({cleanup_error})"
                        )
            done = sum(1 for p in self.pairs if p.status=="FERTIG")
            self.overall_progress.emit(done/max(1,total)*100.0)
        if all(p.status=="FERTIG" for p in self.pairs):
            try:
                dst=get_used_dir(); moved=0
                for p in self.pairs:
                    for f in (p.image_path,p.audio_path):
                        if f and Path(f).exists():
                            safe_move(Path(f), dst, copy_only=self.copy_only); moved+=1
                self.log.emit(f"{moved} Dateien nach {dst} {'kopiert' if self.copy_only else 'verschoben'}.")
            except Exception as e:
                self.log.emit(f"Archivierung fehlgeschlagen: {e}")
        self.finished.emit()

# ---------- UI Widgets ----------
class DropListWidget(QtWidgets.QListWidget):
    files_dropped = Signal(list)
    def __init__(self, title:str, patterns:Tuple[str,...]):
        super().__init__()
        self.patterns=patterns
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setToolTip(title); self.setStatusTip(title)
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
            key=lambda item: self._sort_value(item.data(Qt.UserRole) or "", mode),
            reverse=reverse,
        )
        self.clear()
        for item in items:
            self.addItem(item)
    def _add_sort_menu(self, menu: QtWidgets.QMenu) -> Dict[QAction, Tuple[str, bool]]:
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
    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
        else: super().dragEnterEvent(e)
    def dragMoveEvent(self,e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
        else: super().dragMoveEvent(e)
    def dropEvent(self,e):
        files=[u.toLocalFile() for u in e.mimeData().urls()]
        acc=[f for f in files if Path(f).is_dir() or f.lower().endswith(self.patterns)]
        if acc: self.add_files(acc); self.files_dropped.emit(acc)
        e.acceptProposedAction()
    def startDrag(self, supportedActions):
        item=self.currentItem()
        if not item:
            return
        mime=QtCore.QMimeData()
        mime.setUrls([QtCore.QUrl.fromLocalFile(item.data(Qt.UserRole))])
        drag=QtGui.QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)
    def add_files(self, files:List[str]):
        for f in files:
            it=QtWidgets.QListWidgetItem(Path(f).name); it.setData(Qt.UserRole,f); self.addItem(it)
    def selected_paths(self)->List[str]:
        return [i.data(Qt.UserRole) for i in self.selectedItems()]
    def contextMenuEvent(self,e:QtGui.QContextMenuEvent):
        item=self.itemAt(e.pos())
        if not item:
            return
        path=item.data(Qt.UserRole)
        menu=QtWidgets.QMenu(self)
        act_open=menu.addAction("Im Ordner zeigen")
        act_copy=menu.addAction("Pfad kopieren")
        act_remove=menu.addAction("Entfernen")
        sort_actions = self._add_sort_menu(menu)
        act=menu.exec(e.globalPos())
        if act==act_open:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))
            self.window()._log(f"Im Ordner gezeigt: {path}")
        elif act==act_copy:
            QtWidgets.QApplication.clipboard().setText(str(path))
            self.window()._log(f"Pfad kopiert: {path}")
        elif act==act_remove:
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
    def _open_item(self,item:QtWidgets.QListWidgetItem):
        path=item.data(Qt.UserRole)
        if path:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))
            wnd = self.window()
            if hasattr(wnd, "_log"):
                wnd._log(f"Im Ordner gezeigt: {path}")

class ImageListWidget(DropListWidget):
    add_to_fav = Signal(str)
    def contextMenuEvent(self,e:QtGui.QContextMenuEvent):
        item=self.itemAt(e.pos())
        if not item:
            return
        path=item.data(Qt.UserRole)
        menu=QtWidgets.QMenu(self)
        act_open=menu.addAction("Im Ordner zeigen")
        act_copy=menu.addAction("Pfad kopieren")
        act_fav=menu.addAction("Zu Favoriten")
        act_remove=menu.addAction("Entfernen")
        sort_actions = self._add_sort_menu(menu)
        act=menu.exec(e.globalPos())
        if act==act_open:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))
            self.window()._log(f"Im Ordner gezeigt: {path}")
        elif act==act_copy:
            QtWidgets.QApplication.clipboard().setText(str(path))
            self.window()._log(f"Pfad kopiert: {path}")
        elif act==act_remove:
            self.takeItem(self.row(item))
            self.window()._log(f"Eintrag entfernt: {path}")
            self._notify_structure_update()
        elif act==act_fav:
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
    def contextMenuEvent(self,e:QtGui.QContextMenuEvent):
        item=self.itemAt(e.pos())
        if not item:
            return
        path=item.data(Qt.UserRole)
        menu=QtWidgets.QMenu(self)
        act_open=menu.addAction("Im Ordner zeigen")
        act_copy=menu.addAction("Pfad kopieren")
        act_use=menu.addAction("Zum Arbeitsbereich")
        act_remove=menu.addAction("Entfernen")
        sort_actions = self._add_sort_menu(menu)
        act=menu.exec(e.globalPos())
        if act==act_open:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))
            self.window()._log(f"Im Ordner gezeigt: {path}")
        elif act==act_copy:
            QtWidgets.QApplication.clipboard().setText(str(path))
            self.window()._log(f"Pfad kopiert: {path}")
        elif act==act_use:
            self.use_fav.emit(path)
            self.window()._log(f"Favorit genutzt: {path}")
        elif act==act_remove:
            self.removed.emit(path)
            self.takeItem(self.row(item))
            self.window()._log(f"Favorit entfernt: {path}")
        elif act in sort_actions:
            mode, reverse = sort_actions[act]
            self._sort_items(mode, reverse=reverse)
            self.window()._log("Liste sortiert")
        e.accept()


class HelpPane(QtWidgets.QTextBrowser):
    def __init__(self):
        super().__init__()
        self.setOpenExternalLinks(True)
        self.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHtml(self._html())
    @staticmethod
    def _guide_svg_data() -> str:
        svg = """
        <svg xmlns="http://www.w3.org/2000/svg" width="520" height="120">
          <rect x="10" y="10" width="160" height="100" rx="10" fill="#e8f0fe" stroke="#1a73e8" stroke-width="2"/>
          <rect x="180" y="10" width="160" height="100" rx="10" fill="#e6f4ea" stroke="#137333" stroke-width="2"/>
          <rect x="350" y="10" width="160" height="100" rx="10" fill="#fce8e6" stroke="#c5221f" stroke-width="2"/>
          <text x="90" y="55" font-size="14" text-anchor="middle" fill="#1a73e8">1. Bilder wählen</text>
          <text x="260" y="55" font-size="14" text-anchor="middle" fill="#137333">2. Audios wählen</text>
          <text x="430" y="55" font-size="14" text-anchor="middle" fill="#c5221f">3. Start</text>
          <text x="90" y="80" font-size="11" text-anchor="middle" fill="#1a73e8">Fotos/Ordner</text>
          <text x="260" y="80" font-size="11" text-anchor="middle" fill="#137333">MP3/WAV etc.</text>
          <text x="430" y="80" font-size="11" text-anchor="middle" fill="#c5221f">Videos erzeugen</text>
        </svg>
        """.strip()
        encoded = urllib.parse.quote(svg)
        return f"data:image/svg+xml;utf8,{encoded}"
    def _html(self)->str:
        return (
            "<h2>Bedienhilfe</h2>"
            "<ol>"
            "<li>Bilder oder Ordner sowie Audios hineinziehen</li>"
            "<li>Gewünschten Modus wählen (Standard, Slideshow, Video + Audio, Mehrere Audios)</li>"
            "<li>Mit 'Auto-Paaren' Dateien koppeln oder selbst zuweisen</li>"
            "<li>Einstellungen prüfen und START klicken</li>"
            "</ol>"
            "<ul>"
            "<li>Doppelklick editiert Pfade, Rechtsklick öffnet Menü</li>"
            "<li>Kontextmenü kann Pfad kopieren oder Zeile löschen</li>"
            "<li>Rechtsklick auf die Listen öffnet ein Menü zum Entfernen</li>"
            "<li>Hilfe-Menü zeigt README und Logdatei</li>"
            "<li>Knopf 'Öffnen' zeigt den Ausgabeordner</li>"
            "<li>Tooltips zeigen volle Pfade</li>"
            "<li>Menü 'Optionen' hat einen Debug-Schalter für mehr Meldungen</li>"
            "<li>Mehr Beispiele im Abschnitt 'Weiterführende Befehle' der Anleitung</li>"
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
            "Wähle Audiodateien (z. B. MP3 oder WAV). "
            "Audio ist die Tonspur."
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

class InfoDashboard(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.total_label = QtWidgets.QLabel("0")
        self.total_label.setAccessibleName("Gesamtzahl")
        self.done_label = QtWidgets.QLabel("0")
        self.done_label.setAccessibleName("Fertig")
        self.err_label = QtWidgets.QLabel("0")
        self.err_label.setAccessibleName("Fehler")
        self.ffmpeg_lbl = QtWidgets.QLabel("ffmpeg: ?")
        self.ffmpeg_lbl.setAccessibleName("FFmpeg Status")
        self.env_lbl = QtWidgets.QLabel("Env: OK")
        self.env_lbl.setAccessibleName("Umgebung")
        self.progress = QtWidgets.QProgressBar()
        self.progress.setMaximumWidth(240)
        self.progress.setAccessibleName("Fortschritt gesamt")
        self.mini_log = QtWidgets.QPlainTextEdit()
        self.mini_log.setReadOnly(True)
        self.mini_log.setMaximumBlockCount(300)
        self.mini_log.setFixedHeight(90)
        self.mini_log.setAccessibleName("Kurzprotokoll")
        row=QtWidgets.QHBoxLayout()
        for w in (QtWidgets.QLabel("Gesamt:"), self.total_label,
                  QtWidgets.QLabel("Fertig:"),  self.done_label,
                  QtWidgets.QLabel("Fehler:"),  self.err_label,
                  QtWidgets.QLabel("Progress:"),self.progress,
                  self.ffmpeg_lbl, self.env_lbl):
            row.addWidget(w)
        row.addStretch(1)
        lay=QtWidgets.QVBoxLayout(self); lay.addLayout(row); lay.addWidget(self.mini_log)
    def set_counts(self,t,d,e): self.total_label.setText(str(t)); self.done_label.setText(str(d)); self.err_label.setText(str(e))
    def set_progress(self,v): self.progress.setValue(v)
    def set_env(self,ff_ok,imp_ok=True):
        self.ffmpeg_lbl.setText(f"ffmpeg: {'OK' if ff_ok else 'FEHLT'}")
        self.env_lbl.setText(f"Env: {'OK' if imp_ok else 'FEHLT'}")
    def log(self,msg): self.mini_log.appendPlainText(msg)

# ---------- MainWindow ----------
class MainWindow(QtWidgets.QMainWindow):
    FONT_STEP = 1

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

        self.settings = QtCore.QSettings(str(SETTINGS_FILE), QtCore.QSettings.IniFormat)
        self._font_size = self.settings.value("ui/font_size", 11, int)
        self.debug_mode = self.settings.value("ui/debug", False, bool)
        self.large_controls = self.settings.value("ui/large_controls", False, bool)
        logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        self._audio_player = QtMultimedia.QMediaPlayer(self)
        self._audio_output = QtMultimedia.QAudioOutput(self)
        self._audio_player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(self.settings.value("ui/audio_preview_volume", 0.8, float))
        self._audio_player.errorOccurred.connect(self._on_audio_preview_error)

        self._restore_window_state()

        sys.excepthook = self._global_exception

        self.pairs: List[PairItem] = []
        self.model = PairTableModel(self.pairs)

        ff_ok = check_ffmpeg()
        self.dashboard = InfoDashboard(); self.dashboard.set_env(ff_ok, True)
        if not ff_ok:
            self._show_error_dialog(
                "FFmpeg fehlt",
                "Bitte FFmpeg installieren oder im Setup reparieren, sonst kann kein Video erzeugt werden.",
                QtWidgets.QMessageBox.Warning,
            )

        self.image_list = ImageListWidget("Bilder", (".jpg",".jpeg",".png",".bmp",".webp"))
        self.audio_list = AudioListWidget("Audios", (".mp3",".wav",".flac",".m4a",".aac"))
        self.favorite_list = FavoriteListWidget("Favoriten", (".jpg",".jpeg",".png",".bmp",".webp"))
        self.image_list.add_to_fav.connect(self._add_to_favorites)
        self.favorite_list.use_fav.connect(self._use_favorite)
        self.favorite_list.removed.connect(lambda p: self._log(f"Favorit entfernt: {p}"))
        self.image_list.files_dropped.connect(self._on_images_added)
        self.audio_list.files_dropped.connect(self._on_audios_added)

        pool_tabs = QtWidgets.QTabWidget()
        pool_tabs.setAccessibleName("Datei-Register")
        pool_tabs.setAccessibleDescription("Register für Bilder, Audios und Favoriten")
        pool_tabs.addTab(self.image_list, "Bilder")
        pool_tabs.addTab(self.audio_list, "Audios")
        pool_tabs.addTab(self.favorite_list, "Favoriten")

        pool_box = QtWidgets.QGroupBox("Dateilisten")
        pb_lay = QtWidgets.QVBoxLayout(pool_box)
        pb_lay.addWidget(pool_tabs)

        # aufklappbare Seitenleiste
        self.sidebar = QtWidgets.QDockWidget("Dateilisten", self)
        self.sidebar.setFeatures(
            QtWidgets.QDockWidget.DockWidgetClosable
            | QtWidgets.QDockWidget.DockWidgetMovable
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar)
        self.sidebar.setVisible(
            self.settings.value("ui/show_sidebar", True, bool)
        )

        self.table = QtWidgets.QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._table_menu)
        self.table.setToolTip("Doppelklick: Pfad bearbeiten, Rechtsklick für Menü")
        self.table.setStatusTip("Doppelklick: Pfad bearbeiten, Rechtsklick für Menü")
        self.table.setAccessibleName("Paar-Tabelle")
        self.table.setAccessibleDescription("Liste der Bild- und Audio-Paare")
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setWordWrap(True)

        self.help_pane = HelpPane()
        self.help_pane.setAccessibleName("Hilfe-Bereich")
        self.help_pane.setAccessibleDescription("Kurzanleitung zum Tool")

        # Einstellungen
        self.out_dir_edit  = QtWidgets.QLineEdit(str(self.settings.value("encode/out_dir", default_output_dir(), str)))
        self.out_dir_edit.setPlaceholderText("Zielordner für fertige Videos")
        self.out_dir_edit.setAccessibleName("Zielordner")
        self.out_dir_edit.setAccessibleDescription("Pfad für fertige Videos")
        self.btn_out_open  = QtWidgets.QToolButton(); self.btn_out_open.setText("Öffnen")
        self.btn_out_open.setToolTip("Ausgabeordner im Dateimanager öffnen")
        self.btn_out_open.setAccessibleName("Ordner öffnen")
        self.btn_out_open.setAccessibleDescription("Ordner im Dateimanager anzeigen")
        self.crf_spin      = QtWidgets.QSpinBox(); self.crf_spin.setRange(0,51); self.crf_spin.setValue(self.settings.value("encode/crf",23,int))
        self.crf_spin.setAccessibleName("CRF Qualität")
        self.crf_spin.setAccessibleDescription("Qualität für das Video (0 bis 51)")
        self.preset_combo  = QtWidgets.QComboBox(); self.preset_combo.addItems(
            ["ultrafast","superfast","veryfast","faster","fast","medium","slow","slower","veryslow"])
        self.preset_combo.setCurrentText(self.settings.value("encode/preset","ultrafast",str))
        self.preset_combo.setAccessibleName("Preset")
        self.preset_combo.setAccessibleDescription("Geschwindigkeits-Voreinstellung für die Kodierung")
        self.width_spin    = QtWidgets.QSpinBox(); self.width_spin.setRange(16,7680); self.width_spin.setValue(self.settings.value("encode/width",1920,int))
        self.width_spin.setAccessibleName("Video-Breite")
        self.width_spin.setAccessibleDescription("Breite des Videos in Pixel")
        self.height_spin   = QtWidgets.QSpinBox(); self.height_spin.setRange(16,4320); self.height_spin.setValue(self.settings.value("encode/height",1080,int))
        self.height_spin.setAccessibleName("Video-Höhe")
        self.height_spin.setAccessibleDescription("Höhe des Videos in Pixel")
        self.abitrate_edit = QtWidgets.QLineEdit(self.settings.value("encode/abitrate","192k",str))
        self.abitrate_edit.setPlaceholderText("z.B. 192k")
        self.abitrate_edit.setAccessibleName("Audio-Bitrate")
        self.abitrate_edit.setAccessibleDescription("Audioqualität als Bitrate, zum Beispiel 192k")
        self.mode_combo   = QtWidgets.QComboBox();
        self.mode_combo.addItems(["Standard","Slideshow","Video + Audio","Mehrere Audios, 1 Bild"])
        self.mode_combo.setToolTip("Verarbeitungsmodus wählen")
        self.mode_combo.setCurrentText(self.settings.value("encode/mode","Standard",str))
        self.mode_combo.setAccessibleName("Modus")
        self.mode_combo.setAccessibleDescription("Auswahl des Verarbeitungsmodus")
        self.clear_after   = QtWidgets.QCheckBox("Nach Fertigstellung Listen leeren")
        self.clear_after.setChecked(self.settings.value("ui/clear_after", False, bool))
        self.auto_open_output = QtWidgets.QCheckBox("Ausgabeordner nach Fertigstellung öffnen")
        self.auto_open_output.setChecked(self.settings.value("ui/auto_open_output", True, bool))
        self.auto_open_output.setAccessibleName("Ausgabeordner automatisch öffnen")
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
        self.clear_after.setAccessibleDescription("Nach dem Abschluss alle Listen leeren")

        self.font_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.font_slider.setRange(8, 32)
        self.font_slider.setValue(self._font_size)
        self.font_slider.setAccessibleName("Schriftgrößen-Schieber")
        self.font_slider.setAccessibleDescription("Schriftgröße der Oberfläche einstellen")
        self.font_value_label = QtWidgets.QLabel(str(self._font_size))
        self.font_value_label.setAccessibleName("Schriftgröße Anzeige")
        self.font_slider.valueChanged.connect(self._on_font_slider_changed)
        self.large_controls_toggle = QtWidgets.QCheckBox("Große Bedienelemente (besser klickbar)")
        self.large_controls_toggle.setChecked(self.large_controls)
        self.large_controls_toggle.setToolTip("Buttons, Tabellenzeilen und Text etwas größer")
        self.large_controls_toggle.toggled.connect(self._toggle_large_controls)

        form = QtWidgets.QFormLayout()
        out_wrap_layout = QtWidgets.QHBoxLayout(); out_wrap_layout.setContentsMargins(0,0,0,0)
        out_wrap_layout.addWidget(self.out_dir_edit); out_wrap_layout.addWidget(self.btn_out_open)
        out_wrap = QtWidgets.QWidget(); out_wrap.setLayout(out_wrap_layout)
        self._add_form(form,"Ausgabeordner",out_wrap,"Zielordner für MP4s")
        self._add_form(form,"CRF",self.crf_spin,"Qualität (0=lossless, 23=Standard)")
        self._add_form(form,"Preset",self.preset_combo,"x264 Preset (schneller = größere Datei)")
        self._add_form(form,"Breite",self.width_spin,"Video-Breite in Pixel")
        self._add_form(form,"Höhe",self.height_spin,"Video-Höhe in Pixel")
        self._add_form(form,"Audio-Bitrate",self.abitrate_edit,"z.B. 192k, 256k")
        self._add_form(form,"Modus",self.mode_combo,"z.B. Slideshow oder Video + Audio")
        font_row = QtWidgets.QHBoxLayout()
        font_row.setContentsMargins(0, 0, 0, 0)
        font_row.addWidget(self.font_slider)
        font_row.addWidget(self.font_value_label)
        font_wrap = QtWidgets.QWidget(); font_wrap.setLayout(font_row)
        self._add_form(form, "Schriftgröße", font_wrap, "Schriftgröße der Oberfläche anpassen")
        form.addRow("", self.clear_after)
        form.addRow("", self.auto_open_output)
        form.addRow("", self.auto_save_project)
        form.addRow("", self.large_controls_toggle)

        settings_box = QtWidgets.QGroupBox("Einstellungen")
        settings_box.setLayout(form)

        self.settings_widget = settings_box

        table_box = QtWidgets.QGroupBox("Paare")
        tb_lay = QtWidgets.QVBoxLayout(table_box); tb_lay.addWidget(self.table)

        help_box = QtWidgets.QGroupBox("Hilfe")
        hb_lay = QtWidgets.QVBoxLayout(help_box); hb_lay.addWidget(self.help_pane)
        self.help_box = help_box

        self.structure_tree = QtWidgets.QTreeWidget()
        self.structure_tree.setHeaderLabels(["Pfad"])
        self.structure_tree.setAlternatingRowColors(True)
        self.structure_tree.setAccessibleName("Projektstruktur")
        self.structure_tree.setAccessibleDescription("Baumansicht für Bilder, Audios und Output")
        self.structure_filter = QtWidgets.QComboBox()
        self.structure_filter.addItems(["Alles", "Bilder", "Audios", "Output"])
        self.structure_filter.setAccessibleName("Struktur-Filter")
        self.structure_filter.setAccessibleDescription("Filtert die Projektstruktur nach Bereich")
        self.structure_search = QtWidgets.QLineEdit()
        self.structure_search.setPlaceholderText("Pfad-Filter, z. B. /Projekt oder Ferien")
        self.structure_search.setAccessibleName("Pfad-Filter")
        self.structure_search.setAccessibleDescription("Filtert die Projektstruktur nach Text im Pfad")
        self.structure_clear_btn = QtWidgets.QToolButton()
        self.structure_clear_btn.setText("X")
        self.structure_clear_btn.setToolTip("Pfad-Filter löschen")
        self.structure_clear_btn.setAccessibleName("Pfad-Filter löschen")
        self.structure_clear_btn.clicked.connect(lambda: self.structure_search.setText(""))

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

        left_tabs = QtWidgets.QTabWidget()
        left_tabs.setAccessibleName("Seitenleiste-Register")
        left_tabs.setAccessibleDescription("Register für Dateilisten und Einstellungen")
        left_tabs.addTab(pool_box, "Dateien")
        left_tabs.addTab(self.settings_widget, "Einstellungen")
        left_tabs.addTab(structure_box, "Struktur")
        self.sidebar.setWidget(left_tabs)

        panel_splitter = QtWidgets.QSplitter(Qt.Horizontal)
        panel_splitter.addWidget(table_box)
        panel_splitter.addWidget(help_box)
        panel_splitter.setStretchFactor(0, 3)
        panel_splitter.setStretchFactor(1, 1)

        self.progress_total = QtWidgets.QProgressBar(); self.progress_total.setFormat("%p% gesamt")
        self.progress_total.setAccessibleName("Gesamtfortschritt")
        self.progress_total.setAccessibleDescription("Fortschritt aller Aufgaben")
        self.log_path_label = QtWidgets.QLabel("Log-Pfad:")
        self.log_path_label.setAccessibleName("Log-Pfad Label")
        self.log_path_edit = QtWidgets.QLineEdit(str(LOG_DIR))
        self.log_path_edit.setReadOnly(True)
        self.log_path_edit.setAccessibleName("Log-Pfad")
        self.log_path_edit.setAccessibleDescription("Speicherort der Logdateien")
        self.log_path_edit.setToolTip("Speicherort der Protokolldateien")
        self.log_path_btn = QtWidgets.QPushButton("Pfad kopieren")
        self.log_path_btn.setToolTip("Log-Ordner in die Zwischenablage kopieren")
        self.log_path_btn.clicked.connect(self._copy_log_path)
        log_path_row = QtWidgets.QHBoxLayout()
        log_path_row.addWidget(self.log_path_label)
        log_path_row.addWidget(self.log_path_edit, 1)
        log_path_row.addWidget(self.log_path_btn)
        self.log_edit = QtWidgets.QPlainTextEdit(); self.log_edit.setReadOnly(True); self.log_edit.setMaximumBlockCount(5000)
        self.log_edit.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
        self.log_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.log_edit.setAccessibleName("Protokoll")
        self.log_edit.setAccessibleDescription("Fortlaufende Meldungen des Programms")

        self.log_box = QtWidgets.QGroupBox("Protokoll")
        bl = QtWidgets.QVBoxLayout(self.log_box)
        bl.addWidget(self.progress_total)
        bl.addLayout(log_path_row)
        bl.addWidget(self.log_edit)

        # Log-Bereich flexibel einteilbar
        main_splitter = QtWidgets.QSplitter(Qt.Vertical)
        main_splitter.addWidget(panel_splitter)
        main_splitter.addWidget(self.log_box)
        main_splitter.setStretchFactor(0, 4)
        main_splitter.setStretchFactor(1, 1)

        # Buttons
        self.btn_add_images = QtWidgets.QPushButton("Bilder wählen")
        self.btn_add_audios = QtWidgets.QPushButton("Audios wählen")
        self.btn_auto_pair  = QtWidgets.QPushButton("Auto-Paaren")
        self.btn_clear      = QtWidgets.QPushButton("Alles löschen")
        self.btn_undo       = QtWidgets.QPushButton("Undo")
        self.btn_save       = QtWidgets.QPushButton("Projekt speichern")
        self.btn_load       = QtWidgets.QPushButton("Projekt laden")
        self.btn_encode     = QtWidgets.QPushButton("START")
        self.btn_stop       = QtWidgets.QPushButton("Stop"); self.btn_stop.setEnabled(False)
        self.btn_wizard     = QtWidgets.QPushButton("Geführter Start")

        self.btn_add_images.setToolTip("Bilder (Fotos) auswählen")
        self.btn_add_audios.setToolTip("Audiodateien auswählen")
        self.btn_auto_pair.setToolTip("Bilder und Audios automatisch koppeln")
        self.btn_clear.setToolTip("Listen komplett leeren")
        self.btn_undo.setToolTip("Letzte Änderung rückgängig machen")
        self.btn_save.setToolTip("Aktuellen Stand speichern")
        self.btn_load.setToolTip("Gespeichertes Projekt laden")
        self.btn_encode.setToolTip("Encoding starten")
        self.btn_stop.setToolTip("Aktuellen Vorgang abbrechen")
        self.btn_wizard.setToolTip("Schritt-für-Schritt-Assistent öffnen")

        self.btn_encode.setStyleSheet("font-size:14pt;font-weight:bold;background:#005BBB;color:white;padding:4px 10px;")

        top_buttons = QtWidgets.QGridLayout()
        top_buttons.setSpacing(4)
        top_buttons.setContentsMargins(4, 4, 4, 4)
        btn_defs = [
            (self.btn_add_images, "Bilder oder Ordner auswählen"),
            (self.btn_add_audios, "Audiodateien hinzufügen"),
            (self.btn_auto_pair, "Dateien automatisch koppeln"),
            (self.btn_wizard, "Assistent für Einsteiger öffnen"),
            (self.btn_clear, "Listen komplett leeren"),
            (self.btn_undo, "Letzten Schritt rückgängig"),
            (self.btn_save, "Projekt auf Platte sichern"),
            (self.btn_load, "Gespeichertes Projekt laden"),
            (self.btn_encode, "Videos jetzt erstellen"),
            (self.btn_stop, "Laufenden Vorgang abbrechen"),
        ]
        for i, (btn, tip) in enumerate(btn_defs):
            row, col = divmod(i, 3)
            top_buttons.addWidget(self._wrap_button(btn, tip), row, col)
        for i in range(3):
            top_buttons.setColumnStretch(i, 1)
        btn_box = QtWidgets.QGroupBox("Aktionen")
        btn_box.setLayout(top_buttons)

        central_layout = QtWidgets.QVBoxLayout()
        central_layout.addWidget(self.dashboard)
        central_layout.addWidget(btn_box)
        central_layout.addWidget(main_splitter)
        central = QtWidgets.QWidget(); central.setLayout(central_layout)
        self.setCentralWidget(central)

        self.count_label = QtWidgets.QLabel("0 Bilder | 0 Audios | 0 Paare")
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
        self.auto_open_output.toggled.connect(self._toggle_auto_open_output)
        self.auto_save_project.toggled.connect(self._toggle_auto_save_project)
        self.mode_combo.currentTextChanged.connect(self._update_default_mode)
        self.structure_filter.currentTextChanged.connect(self._apply_structure_filter)
        self.structure_search.textChanged.connect(self._apply_structure_filter)
        self.out_dir_edit.editingFinished.connect(self._refresh_structure_view)

        self._set_font(self._font_size)
        self._apply_theme(self.settings.value("ui/theme", "Modern"))
        self._apply_large_controls(self.large_controls)
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

    # ----- UI helpers -----
    def _build_menus(self):
        menubar = self.menuBar()

        m_datei = menubar.addMenu("Datei")
        act_load = QAction("Projekt laden", self)
        act_load.setToolTip("Gespeichertes Projekt laden")
        act_load.setShortcut(QtGui.QKeySequence("Ctrl+O"))
        act_load.triggered.connect(self._load_project)
        m_datei.addAction(act_load)
        act_save = QAction("Projekt speichern", self)
        act_save.setToolTip("Projekt sichern")
        act_save.setShortcut(QtGui.QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self._save_project)
        m_datei.addAction(act_save)
        act_quit = QAction("Beenden", self); act_quit.setToolTip("Programm schließen"); act_quit.triggered.connect(self.close)
        m_datei.addAction(act_quit)

        m_ansicht = menubar.addMenu("Ansicht")
        act_font_plus  = QAction("Schrift +", self);  act_font_plus.setToolTip("Schriftgröße erhöhen"); act_font_plus.triggered.connect(lambda: self._change_font(1))
        act_font_minus = QAction("Schrift -", self);  act_font_minus.setToolTip("Schriftgröße verkleinern"); act_font_minus.triggered.connect(lambda: self._change_font(-1))
        act_font_reset = QAction("Schrift Reset", self); act_font_reset.setToolTip("Schriftgröße zurücksetzen"); act_font_reset.triggered.connect(lambda: self._set_font(11))
        m_ansicht.addActions([act_font_plus, act_font_minus, act_font_reset])
        self.act_show_help = QAction("Hilfe-Bereich", self, checkable=True,
                                     checked=self.settings.value("ui/show_help", True, bool))
        self.act_show_help.toggled.connect(self._toggle_help)
        m_ansicht.addAction(self.act_show_help)
        self.act_show_log = QAction("Log-Bereich", self, checkable=True,
                                    checked=self.settings.value("ui/show_log", True, bool))
        self.act_show_log.toggled.connect(self._toggle_log)
        m_ansicht.addAction(self.act_show_log)
        self.act_show_sidebar = QAction("Sidebar", self, checkable=True,
                                        checked=self.sidebar.isVisible())
        self.act_show_sidebar.toggled.connect(self._toggle_sidebar)
        m_ansicht.addAction(self.act_show_sidebar)

        m_theme = menubar.addMenu("Theme")
        for name in THEMES.keys():
            act = QAction(name, self)
            act.triggered.connect(lambda _=False, n=name: self._apply_theme(n))
            m_theme.addAction(act)

        m_option = menubar.addMenu("Optionen")
        self.act_copy_only = QAction("Dateien nur kopieren (nicht verschieben)", self, checkable=True, checked=self.copy_only)
        self.act_copy_only.setToolTip("Originaldateien behalten")
        self.act_copy_only.triggered.connect(self._toggle_copy_mode)
        m_option.addAction(self.act_copy_only)
        self.act_debug = QAction("Debug-Log", self, checkable=True, checked=self.debug_mode)
        self.act_debug.setToolTip("Detailiertes Protokoll aktivieren")
        self.act_debug.triggered.connect(self._toggle_debug)
        m_option.addAction(self.act_debug)

        m_hilfe = menubar.addMenu("Hilfe")
        act_doc = QAction("README öffnen", self); act_doc.setToolTip("Dokumentation anzeigen"); act_doc.triggered.connect(self._open_readme)
        act_log = QAction("Logdatei öffnen", self); act_log.setToolTip("Letzte Meldungen anzeigen"); act_log.triggered.connect(self._open_logfile)
        act_help = QAction("Kurzanleitung", self); act_help.setToolTip("Kurzes Hilfefenster anzeigen"); act_help.triggered.connect(self._show_help_window)
        act_wizard = QAction("Geführter Start", self); act_wizard.setToolTip("Schritt-für-Schritt-Assistent öffnen"); act_wizard.triggered.connect(self._show_guided_wizard)
        m_hilfe.addAction(act_doc)
        m_hilfe.addAction(act_log)
        m_hilfe.addAction(act_help)
        m_hilfe.addAction(act_wizard)

    def _change_font(self, delta:int):
        self._set_font(self._font_size + delta)

    def _on_font_slider_changed(self, value: int):
        self.font_value_label.setText(str(value))
        self._set_font(value)

    def _set_font(self, size:int):
        size = max(8, min(32, size))
        self._font_size = size
        self._apply_font()
        if hasattr(self, "font_slider") and self.font_slider.value() != size:
            self.font_slider.setValue(size)
        if hasattr(self, "font_value_label"):
            self.font_value_label.setText(str(size))
        self.settings.setValue("ui/font_size", size)
        self._log(f"Schriftgröße gesetzt auf {size}")

    def _apply_font(self):
        f = QtGui.QFont("DejaVu Sans", self._font_size)
        self.setFont(f)

    def _apply_theme(self, name: str):
        css = THEMES.get(name, "")
        QtWidgets.QApplication.instance().setStyleSheet(css)
        self.settings.setValue("ui/theme", name)
        self._log(f"Theme gewechselt: {name}")

    def _open_out_dir(self):
        path = self.out_dir_edit.text().strip()
        if not path:
            self._log("Ausgabeordner fehlt.", logging.WARNING)
            QtWidgets.QMessageBox.information(
                self, "Ausgabeordner fehlt", "Bitte zuerst einen Ausgabeordner festlegen."
            )
            return
        out_path = Path(path).expanduser()
        try:
            out_path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            self._log(f"Ausgabeordner konnte nicht erstellt werden: {exc}", logging.ERROR)
            QtWidgets.QMessageBox.critical(
                self, "Ausgabeordner fehlerhaft", f"Ordner konnte nicht erstellt werden:\n{exc}"
            )
            return
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(out_path)))
        self._log(f"Ausgabeordner geöffnet: {out_path}")

    def _open_readme(self):
        path = str(Path('README.md').resolve())
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
        self._log("README geöffnet")

    def _open_logfile(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(LOG_FILE)))
        self._log("Logdatei geöffnet")

    def _copy_log_path(self):
        QtWidgets.QApplication.clipboard().setText(str(LOG_DIR))
        self._log(f"Log-Pfad kopiert: {LOG_DIR}")

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

    def _add_form(self, layout: QtWidgets.QFormLayout, label: str, widget: QtWidgets.QWidget, help_text: str):
        widget.setToolTip(help_text); widget.setStatusTip(help_text)
        hint = QtWidgets.QLabel(f"<small>{help_text}</small>"); hint.setWordWrap(True)
        box = QtWidgets.QVBoxLayout(); box.addWidget(widget); box.addWidget(hint)
        wrap = QtWidgets.QWidget(); wrap.setLayout(box)
        layout.addRow(label, wrap)

    def _wrap_button(self, button: QtWidgets.QAbstractButton, help_text: str) -> QtWidgets.QWidget:
        """Return button with help label underneath."""
        button.setToolTip(help_text)
        button.setStatusTip(help_text)
        button.setAccessibleName(button.text())
        button.setAccessibleDescription(help_text)
        lbl = QtWidgets.QLabel(f"<small>{help_text}</small>"); lbl.setAlignment(Qt.AlignCenter)
        button.setMaximumHeight(28)
        box = QtWidgets.QVBoxLayout(); box.setContentsMargins(2, 0, 2, 0)
        box.setSpacing(1)
        box.addWidget(button); box.addWidget(lbl)
        w = QtWidgets.QWidget(); w.setLayout(box)
        return w

    def _log(self, msg:str, level=logging.INFO):
        if level >= logging.INFO or self.debug_mode:
            self.log_edit.appendPlainText(msg)
            self.dashboard.log(msg)
        logger.log(level, msg)

    def _log_details(self, max_chars: int = 4000) -> str:
        try:
            text = LOG_FILE.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"Logdatei: {LOG_FILE}\nKonnte Log nicht lesen: {e}"
        if len(text) > max_chars:
            text = "... (gekürzt)\n" + text[-max_chars:]
        return f"Logdatei: {LOG_FILE}\n\n{text}"

    def _on_audio_preview_error(self, error, error_string) -> None:
        if error:
            self._log(f"Audio-Vorschau Fehler: {error_string}", logging.ERROR)

    def _play_audio_preview(self, path: str) -> None:
        if not path:
            return
        file_path = Path(path)
        if not file_path.exists():
            self._show_error_dialog(
                "Audio fehlt",
                f"Die Audiodatei wurde nicht gefunden: {file_path}",
                QtWidgets.QMessageBox.Warning,
            )
            return
        self._audio_player.setSource(QtCore.QUrl.fromLocalFile(str(file_path)))
        self._audio_player.play()
        self._log(f"Audio-Vorschau gestartet: {file_path.name}")

    def _stop_audio_preview(self) -> None:
        if self._audio_player.playbackState() != QtMultimedia.QMediaPlayer.StoppedState:
            self._audio_player.stop()
            self._log("Audio-Vorschau gestoppt")

    def _restore_window_state(self) -> None:
        geometry = self.settings.value("ui/window_geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = self.settings.value("ui/window_state")
        if state:
            self.restoreState(state)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.settings.setValue("ui/window_geometry", self.saveGeometry())
        self.settings.setValue("ui/window_state", self.saveState())
        self._stop_audio_preview()
        super().closeEvent(event)

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

    def _debug(self, msg:str):
        self._log(f"DEBUG: {msg}", logging.DEBUG)

    def _get_last_dir(self, key: str, fallback: Path) -> str:
        value = self.settings.value(key, "", str)
        if value:
            stored = Path(value)
            if stored.exists():
                return str(stored)
        return str(fallback)

    def _set_last_dir(self, key: str, path: Path | str) -> None:
        if not path:
            return
        stored = Path(path).expanduser()
        if stored.is_file():
            stored = stored.parent
        self.settings.setValue(key, str(stored))

    def _set_last_project_path(self, path: str) -> None:
        if not path:
            return
        project_path = Path(path).expanduser()
        self.settings.setValue("ui/last_project_path", str(project_path))
        self.settings.setValue("ui/last_project_dir", str(project_path.parent))

    def _project_payload(self) -> Dict[str, Any]:
        return {
            "pairs": [
                {"image": p.image_path, "audio": p.audio_path, "output": p.output}
                for p in self.pairs
            ],
            "settings": self._gather_settings(),
        }

    def _auto_save_project(self, reason: str) -> None:
        if not self.auto_save_project.isChecked():
            return
        auto_path = self.settings.value("ui/auto_save_path", "", str)
        if not auto_path:
            auto_path = str(Path.home() / "videobatch_autosave.json")
            self.settings.setValue("ui/auto_save_path", auto_path)
        try:
            Path(auto_path).write_text(
                json.dumps(self._project_payload(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            self._log(f"Auto-Speichern fehlgeschlagen ({reason}): {exc}", logging.ERROR)
            return
        self._log(f"Auto-Speichern ok ({reason}): {auto_path}")

    def _push_history(self):
        snap=[]
        for p in self.pairs:
            q=PairItem(p.image_path,p.audio_path)
            q.duration=p.duration; q.output=p.output; q.status=p.status
            q.progress=p.progress; q.valid=p.valid; q.validation_msg=p.validation_msg
            snap.append(q)
        self._history.append(snap)
        if len(self._history)>30: self._history.pop(0)

    def _update_counts(self):
        img_count = self.image_list.count()
        aud_count = self.audio_list.count()
        pair_count = sum(1 for p in self.pairs if p.image_path and p.audio_path)
        err_count  = sum(1 for p in self.pairs if p.status == "FEHLER")
        fin_count  = sum(1 for p in self.pairs if p.status == "FERTIG")
        self.count_label.setText(f"{img_count} Bilder | {aud_count} Audios | {pair_count} Paare")
        self.dashboard.set_counts(pair_count, fin_count, err_count)

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

        def add_path_items(root: QtWidgets.QTreeWidgetItem, paths: List[str]) -> None:
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
                        for p in sorted(out_path.iterdir())
                        if p.is_file() and p.suffix.lower() in OUTPUT_EXTENSIONS
                    ]
                except Exception as exc:
                    error_item = QtWidgets.QTreeWidgetItem([f"Fehler beim Lesen: {exc}"])
                    output_root.addChild(error_item)
            else:
                hint_item = QtWidgets.QTreeWidgetItem(["Ordner existiert noch nicht."])
                output_root.addChild(hint_item)
        else:
            hint_item = QtWidgets.QTreeWidgetItem(["Kein Ausgabeordner gesetzt."])
            output_root.addChild(hint_item)

        max_outputs = 200
        for path in output_files[:max_outputs]:
            item = QtWidgets.QTreeWidgetItem([path])
            item.setData(0, Qt.UserRole, path)
            output_root.addChild(item)
        if len(output_files) > max_outputs:
            output_root.addChild(
                QtWidgets.QTreeWidgetItem([f"… weitere {len(output_files) - max_outputs} Dateien"])
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
                path_text = (child.data(0, Qt.UserRole) or child.text(0)).lower()
                matches = (not search_text) or (search_text in path_text)
                child_visible = allow_category and matches
                child.setHidden(not child_visible)
                if child_visible:
                    visible_children += 1
            root.setHidden(not allow_category or visible_children == 0)

    # ----- file actions -----
    def _select_files(self, title: str, start_dir: str, filters: List[str]) -> List[str]:
        dialog = QtWidgets.QFileDialog(self, title, start_dir)
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        dialog.setOption(QtWidgets.QFileDialog.ReadOnly, True)
        dialog.setNameFilters(filters)
        dialog.selectNameFilter(filters[0])
        if dialog.exec():
            return dialog.selectedFiles()
        return []

    def _pick_images(self):
        mode=self.mode_combo.currentText()
        start_dir = self._get_last_dir("ui/last_image_dir", Path.cwd())
        if mode=="Slideshow":
            d=QtWidgets.QFileDialog.getExistingDirectory(self,"Ordner mit Bildern wählen",start_dir)
            if d:
                self._set_last_dir("ui/last_image_dir", d)
                self._on_images_added([d])
        else:
            files = self._select_files(
                "Bilder wählen",
                start_dir,
                [
                    "Alle Medien (*.jpg *.jpeg *.png *.bmp *.webp *.mp4 *.mkv *.avi *.mov)",
                    "Bilder (*.jpg *.jpeg *.png *.bmp *.webp)",
                    "Videos (*.mp4 *.mkv *.avi *.mov)",
                ],
            )
            if files:
                self._set_last_dir("ui/last_image_dir", Path(files[0]).parent)
                self._on_images_added(files)
    def _pick_audios(self):
        start_dir = self._get_last_dir("ui/last_audio_dir", Path.cwd())
        files = self._select_files(
            "Audios wählen",
            start_dir,
            [
                "Audios (*.mp3 *.wav *.flac *.m4a *.aac)",
                "Alle Dateien (*.*)",
            ],
        )
        if files:
            self._set_last_dir("ui/last_audio_dir", Path(files[0]).parent)
            self._on_audios_added(files)
    def _pick_image_folder(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Bildordner wählen", str(Path.cwd()))
        if not d:
            return
        files = self._collect_media_files(Path(d), (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".mp4", ".mkv", ".avi", ".mov"))
        if not files:
            QtWidgets.QMessageBox.information(self, "Keine Bilder", "Im Ordner wurden keine Bilddateien gefunden.")
            return
        self._on_images_added([str(f) for f in files])

    def _pick_audio_folder(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Audioordner wählen", str(Path.cwd()))
        if not d:
            return
        files = self._collect_media_files(Path(d), (".mp3", ".wav", ".flac", ".m4a", ".aac"))
        if not files:
            QtWidgets.QMessageBox.information(self, "Keine Audios", "Im Ordner wurden keine Audiodateien gefunden.")
            return
        self._on_audios_added([str(f) for f in files])

    def _collect_media_files(self, folder: Path, suffixes: Tuple[str, ...]) -> List[Path]:
        if not folder.exists() or not folder.is_dir():
            return []
        files = [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in suffixes]
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
        it=iter(files)
        for p in self.pairs:
            if p.audio_path is None:
                try: p.audio_path=next(it); p.update_duration(); p.validate()
                except StopIteration: break
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
        imgs=[self.image_list.item(i).data(Qt.UserRole) for i in range(self.image_list.count())]
        auds=[self.audio_list.item(i).data(Qt.UserRole) for i in range(self.audio_list.count())]
        imgs.sort(); auds.sort()
        self._debug(f"Auto-Pair start mit {len(imgs)} Bild(er) und {len(auds)} Audio(s)")
        self.model.clear()
        new=[]
        mode=self.mode_combo.currentText()
        if mode=="Mehrere Audios, 1 Bild" and imgs:
            img = imgs[0]
            for aud in auds:
                p = PairItem(img, aud); p.update_duration(); p.validate(); new.append(p)
        elif mode=="Slideshow":
            if len(imgs)==len(auds):
                pairs = zip(imgs, auds)
            elif len(imgs)==1:
                pairs = ((imgs[0], a) for a in auds)
            else:
                pairs = zip(imgs, auds)
            for img, aud in pairs:
                p = PairItem(img, aud); p.update_duration(); p.validate(); new.append(p)
        else:
            for img, aud in zip(imgs, auds):
                p = PairItem(img, aud); p.update_duration(); p.validate(); new.append(p)
        self.model.add_pairs(new)
        self._debug(f"Auto-Pair Ergebnis: {[(p.image_path, p.audio_path) for p in new][:3]} ...")
        self._update_counts()
        self._resize_columns()
        self._log(f"Auto-Pair erstellt {len(new)} Paar(e)")

    def _clear_all(self):
        if QtWidgets.QMessageBox.question(self,"Löschen?","Alle Paare wirklich entfernen?")!=QtWidgets.QMessageBox.Yes: return
        self._push_history()
        self.model.clear(); self.image_list.clear(); self.audio_list.clear()
        self.log_edit.clear(); self.dashboard.mini_log.clear()
        self._update_counts()
        self._refresh_structure_view()
        self._log("Listen geleert")

    def _undo_last(self):
        if not self._history: return
        last=self._history.pop()
        self.model.clear(); self.model.add_pairs(last)
        self._update_counts()
        self._resize_columns()
        self._refresh_structure_view()
        self._log("Rückgängig ausgeführt")

    # ----- save / load -----
    def _save_project(self):
        start_dir = self._get_last_dir("ui/last_project_dir", Path.cwd())
        start_path = str(Path(start_dir) / "projekt.json")
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,"Projekt speichern",start_path,"JSON (*.json)")
        if not path: return
        data = self._project_payload()
        data={"pairs":[{"image":p.image_path,"audio":p.audio_path,"output":p.output} for p in self.pairs],
              "settings":self._gather_settings(require_valid=False)}
        try:
            Path(path).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
        except Exception as e:
            self._show_error_dialog("Fehler beim Speichern", str(e))
            self._log(f"Fehler beim Speichern: {e}")
            return
        self._set_last_project_path(path)
        self._refresh_structure_view()
        self._log(f"Projekt gespeichert: {path}")

    def _load_project(self):
        start_dir = self._get_last_dir("ui/last_project_dir", Path.cwd())
        path,_ = QtWidgets.QFileDialog.getOpenFileName(self, "Projekt laden", start_dir, "JSON (*.json)")
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as e:
            self._show_error_dialog("Fehler beim Laden", str(e))
            self._log(f"Fehler beim Laden: {e}")
            return
        self._set_last_project_path(path)
        self._push_history()
        self.model.clear()
        new=[]
        for d in data.get("pairs",[]):
            p=PairItem(d.get("image",""),d.get("audio"))
            p.output=d.get("output",""); p.update_duration(); p.validate(); new.append(p)
        self.model.add_pairs(new)
        s=data.get("settings",{})
        self.out_dir_edit.setText(s.get("out_dir", self.out_dir_edit.text()))
        self.crf_spin.setValue(s.get("crf", self.crf_spin.value()))
        self.preset_combo.setCurrentText(s.get("preset", self.preset_combo.currentText()))
        self.width_spin.setValue(s.get("width", self.width_spin.value()))
        self.height_spin.setValue(s.get("height", self.height_spin.value()))
        self.abitrate_edit.setText(s.get("abitrate", self.abitrate_edit.text()))
        self.mode_combo.setCurrentText(s.get("mode", self.mode_combo.currentText()))
        self._update_counts()
        self._resize_columns()
        self._refresh_structure_view()
        self._log(f"Projekt geladen: {path}")

    # ----- encode -----
    def _gather_settings(self, require_valid: bool = True) -> Optional[Dict[str, Any]]:
        abitrate = self.abitrate_edit.text().strip() or "192k"
        if not re.match(r"^\d+(k|M)$", abitrate):
            msg = (
                "Bitte eine Audiobitrate wie 192k oder 2M eingeben. "
                "Die Zahl ist die Datenmenge pro Sekunde, k=Kilobit, M=Megabit."
            )
            if require_valid:
                QtWidgets.QMessageBox.warning(self, "Ungültige Audiobitrate", msg)
                self._log("Abbruch: Audiobitrate ist ungültig.")
                return None
            self._log("Hinweis: Ungültige Audiobitrate erkannt, setze Standard 192k.")
            abitrate = "192k"
        return {"out_dir": self.out_dir_edit.text().strip(),
                "crf": self.crf_spin.value(),
                "preset": self.preset_combo.currentText(),
                "width": self.width_spin.value(),
                "height": self.height_spin.value(),
                "abitrate": abitrate,
                "mode": self.mode_combo.currentText()}

    def _dir_has_slideshow_images(self, path: Path) -> bool:
        try:
            for entry in path.iterdir():
                if entry.is_file() and entry.suffix.lower() in SLIDESHOW_IMAGE_EXTENSIONS:
                    return True
        except Exception:
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
        self._log(f"Fehler in Zeile {row+1}: {msg}")
        self._update_counts()

    def _start_encode(self):
        settings = self._gather_settings()
        if settings is None:
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
            QtWidgets.QMessageBox.warning(self, "Fehlende Audios", "Nicht alle Bilder haben ein Audio.")
            self._log("Encoding abgebrochen: nicht alle Bilder haben ein Audio.")
            return
        mode = settings.get("mode", "Standard")
        if mode == "Mehrere Audios, 1 Bild":
            if self.image_list.count() == 0:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Bild fehlt",
                    "Für diesen Modus wird mindestens ein Bild benötigt.",
                )
                self._log("Encoding abgebrochen: kein Bild für 'Mehrere Audios, 1 Bild'.")
                return
        if mode == "Slideshow":
            invalid_rows = False
            for idx, p in enumerate(self.pairs):
                img_path = Path(p.image_path) if p.image_path else None
                if not img_path or not img_path.is_dir():
                    self._flag_row_error(idx, "Slideshow benötigt einen Ordner mit Bildern.")
                    invalid_rows = True
                    continue
                if not self._dir_has_slideshow_images(img_path):
                    self._flag_row_error(idx, "Im Bildordner sind keine Bilddateien vorhanden.")
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
        invalid=[(i, p) for i, p in enumerate(self.pairs) if not p.valid]
            self._suggest_add_audios()
            return
        for p in self.pairs: p.validate()
        invalid=[p for p in self.pairs if not p.valid]
        if invalid:
            row = self.pairs.index(invalid[0])
            idx = self.model.index(row, 0)
            sel = self.table.selectionModel()
            if sel is not None:
                sel.select(idx, QtCore.QItemSelectionModel.ClearAndSelect | QtCore.QItemSelectionModel.Rows)
                self.table.setCurrentIndex(idx)
            self.table.scrollTo(idx, QtWidgets.QAbstractItemView.PositionAtCenter)
            self.table.setFocus()
            self._show_error_dialog("Validierungsfehler", invalid[0].validation_msg)
            first_row, first_item = invalid[0]
            for row, item in invalid:
                self._flag_row_error(row, item.validation_msg)
            QtWidgets.QMessageBox.critical(self, "Validierungsfehler", first_item.validation_msg)
            return
        out_dir = Path(self.out_dir_edit.text().strip())
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            test_file = out_dir/".write_test"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            self._show_error_dialog("Ordnerproblem", str(e))
            self._log(f"Encoding abgebrochen: Ordnerproblem ({e})")
            return
        self.btn_encode.setEnabled(False); self.btn_stop.setEnabled(True)
        self.progress_total.setValue(0); self.dashboard.set_progress(0); self._log("Starte Encoding …")
        self.worker = EncodeWorker(self.pairs, settings, self.copy_only)
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
        msg.setWindowTitle("Bilder fehlen")
        msg.setText("Bitte zuerst Bilder auswählen.")
        msg.setInformativeText("Tipp: Du kannst einzelne Dateien oder einen Ordner wählen.")
        btn_files = msg.addButton("Bilder wählen", QtWidgets.QMessageBox.AcceptRole)
        btn_folder = msg.addButton("Bildordner wählen", QtWidgets.QMessageBox.ActionRole)
        msg.addButton("Abbrechen", QtWidgets.QMessageBox.RejectRole)
        msg.exec()
        if msg.clickedButton() == btn_files:
            self._pick_images()
        elif msg.clickedButton() == btn_folder:
            self._pick_image_folder()

    def _suggest_add_audios(self):
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Audios fehlen")
        msg.setText("Bitte Audiodateien auswählen.")
        msg.setInformativeText("Tipp: Ein Audio pro Bild, oder nutze den Modus 'Mehrere Audios, 1 Bild'.")
        btn_files = msg.addButton("Audios wählen", QtWidgets.QMessageBox.AcceptRole)
        btn_folder = msg.addButton("Audioordner wählen", QtWidgets.QMessageBox.ActionRole)
        msg.addButton("Abbrechen", QtWidgets.QMessageBox.RejectRole)
        msg.exec()
        if msg.clickedButton() == btn_files:
            self._pick_audios()
        elif msg.clickedButton() == btn_folder:
            self._pick_audio_folder()

    def _stop_encode(self):
        if self.worker: self.worker.stop()
        self.btn_stop.setEnabled(False)
        self._log("Encoding gestoppt")

    def _on_row_progress(self,row:int,perc:float):
        if 0<=row<len(self.pairs):
            self.pairs[row].progress=perc
            idx=self.model.index(row,6); self.model.dataChanged.emit(idx,idx)

    def _on_overall_progress(self,perc:float):
        v=int(perc); self.progress_total.setValue(v); self.dashboard.set_progress(v)

    def _on_row_error(self,row:int,msg:str):
        msg = self._normalize_error_message(msg)
        self._log(f"Fehler in Zeile {row+1}: {msg}")
        if 0<=row<len(self.pairs):
            self.pairs[row].status="FEHLER"
            idx=self.model.index(row,7); self.model.dataChanged.emit(idx,idx)
            self.table.scrollTo(idx, QtWidgets.QAbstractItemView.PositionAtCenter)
        self._show_error_dialog("Fehler in Zeile", msg)
        self._update_counts()
        self._flag_row_error(row, msg)

    def _encode_finished(self):
        self.btn_encode.setEnabled(True); self.btn_stop.setEnabled(False)
        self.progress_total.setValue(100); self.dashboard.set_progress(100)
        self._log("Alle Jobs abgeschlossen.")
        if self.thread:
            self.thread.quit(); self.thread.wait()
        self.thread=None; self.worker=None
        self._update_counts()
        if self.auto_open_output.isChecked():
            self._open_out_dir()
        if self.clear_after.isChecked():
            self._clear_all()

    # ----- misc -----
    def _toggle_copy_mode(self, checked: bool):
        self.copy_only=checked
        self._log(f"Archivmodus: Dateien werden {'kopiert' if checked else 'verschoben'}.")

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
        self.debug_mode = checked
        logger.setLevel(logging.DEBUG if checked else logging.INFO)
        self.settings.setValue("ui/debug", checked)
        self._log(f"Debug-Log {'aktiviert' if checked else 'deaktiviert'}")

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
    def _toggle_large_controls(self, checked: bool):
        self.large_controls = checked
        self.settings.setValue("ui/large_controls", checked)
        self._apply_large_controls(checked)
        self._log(f"Große Bedienelemente {'aktiviert' if checked else 'deaktiviert'}")

    def _apply_large_controls(self, enabled: bool):
        height = 40 if enabled else 28
        font_size = self._font_size + (2 if enabled else 0)
        buttons = [
            self.btn_add_images, self.btn_add_audios, self.btn_auto_pair, self.btn_clear,
            self.btn_undo, self.btn_save, self.btn_load, self.btn_encode, self.btn_stop,
            self.btn_wizard, self.btn_out_open,
        ]
        for btn in buttons:
            btn.setMinimumHeight(height)
            btn.setFont(QtGui.QFont("DejaVu Sans", font_size))
        self.table.verticalHeader().setDefaultSectionSize(36 if enabled else 24)
        self.log_edit.setFont(QtGui.QFont("DejaVu Sans", font_size))

    def _global_exception(self, etype, value, tb):
        import traceback
        msg = "".join(traceback.format_exception(etype, value, tb))
        self._log(msg, logging.ERROR)
        short = msg if len(msg) < 1000 else msg[:1000] + "\n...\nSiehe Logdatei für Details."
        self._show_error_dialog("Unerwarteter Fehler", short)

    def _resize_columns(self):
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._resize_columns()

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
                self.statusBar().showMessage("Pfad kopiert", 2000)
                self._log(f"Pfad kopiert: {path}")
        elif action == act_remove:
            self._push_history()
            self.model.remove_rows([row])
            self._update_counts()
            self._resize_columns()
            self._log(f"Zeile {row+1} gelöscht")

    def _show_statusbar_path(self, index: QtCore.QModelIndex):
        if not index.isValid(): return
        if index.column() in (2,3,5):
            self.statusBar().showMessage(self.model.data(index, Qt.DisplayRole), 5000)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.settings.setValue("ui/geometry", self.saveGeometry())
        self.settings.setValue("ui/window_state", self.saveState())
        self.settings.setValue("ui/clear_after", self.clear_after.isChecked())
        self.settings.setValue("ui/auto_open_output", self.auto_open_output.isChecked())
        self.settings.setValue("ui/auto_save_project", self.auto_save_project.isChecked())
        s = self._gather_settings(require_valid=False)
        self.settings.setValue("ui/large_controls", self.large_controls)
        s = self._gather_settings()
        self.settings.setValue("encode/out_dir", s["out_dir"])
        self.settings.setValue("encode/crf", s["crf"])
        self.settings.setValue("encode/preset", s["preset"])
        self.settings.setValue("encode/width", s["width"])
        self.settings.setValue("encode/height", s["height"])
        self.settings.setValue("encode/abitrate", s["abitrate"])
        self.settings.setValue("encode/mode", s["mode"])
        if self.auto_save_project.isChecked():
            self._auto_save_project("Schließen")
        super().closeEvent(event)

# ---- Public
def run_gui():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    if QtWidgets.QApplication.instance() is app:
        sys.exit(app.exec())

if __name__ == "__main__":
    run_gui()
