# =========================================
# QUICKSTART
# Direktstart (wenn alles installiert):  python3 videobatch_gui.py
# Empfohlen (Auto-Setup):                python3 videobatch_launcher.py
# Edit mit micro:                        micro videobatch_gui.py
# =========================================

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHeaderView

# ---------- Logging ----------
LOG_DIR = Path.home()/".videobatchtool"/"logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
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
THEMES = {
    "Standard": "",
    "Dunkel": (
        "QWidget{background-color:#2b2b2b;color:#ffffff;} "
        "QPushButton{background-color:#444;color:white;}"
    ),
    "Blau": (
        "QWidget{background-color:#1e1e2d;color:#c7d8f4;} "
        "QPushButton{background-color:#3d59ab;color:white;}"
    ),
    "Gruen": (
        "QWidget{background-color:#28342b;color:#d4ffd4;} "
        "QPushButton{background-color:#385b3c;color:white;}"
    ),
    "Retro": (
        "QWidget{background-color:#f5deb3;color:#00008b;} "
        "QPushButton{background-color:#cd853f;color:black;}"
    ),
    "Kontrast": (
        "QWidget{background-color:#000;color:#ffff00;} "
        "QPushButton{background-color:#000;color:#ffff00;border:1px solid #ffff00;}"
    ),
    "Modern": (
        "QWidget{background-color:#f0f0f0;color:#202020;} "
        "QPushButton{background-color:#2074d4;color:white;border-radius:4px;padding:4px 10px;} "
        "QGroupBox{border:1px solid #a0a0a0;margin-top:6px;} "
        "QGroupBox::title{left:8px;subcontrol-origin:margin;font-weight:bold;color:#202020;}"
    ),
}

# ---------- Helpers ----------
def which(p: str): return shutil.which(p)
def check_ffmpeg(): return which("ffmpeg") and which("ffprobe")
def human_time(sec: float) -> str:
    sec = int(sec); m, s = divmod(sec, 60); h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def probe_duration(path: str) -> float:
    try:
        import ffmpeg
        pr = ffmpeg.probe(path)
        fmt = pr.get("format", {})
        if "duration" in fmt: return float(fmt["duration"])
        for st in pr.get("streams", []):
            if st.get("codec_type") == "audio":
                return float(st.get("duration", 0) or 0)
    except Exception as e:
        print("Fehler beim Prüfen der Dauer:", e, file=sys.stderr)
    return 0.0

def get_used_dir() -> Path:
    return Path.home() / "benutzte_dateien"

def default_output_dir() -> Path:
    return Path.home() / "Videos" / "VideoBatchTool_Out"

def safe_move(src: Path, dst_dir: Path, copy_only: bool=False) -> Path:
    dst_dir.mkdir(parents=True, exist_ok=True)
    tgt = dst_dir / src.name
    if tgt.exists():
        stem, suf = src.stem, src.suffix
        tgt = dst_dir / f"{stem}_{datetime.now().strftime('%Y%m%d-%H%M%S')}{suf}"
    try:
        if copy_only: shutil.copy2(src, tgt)
        else: shutil.move(src, tgt)
    except Exception:
        shutil.copy2(src, tgt)
        if not copy_only:
            try: src.unlink()
            except Exception as e:
                print("Fehler beim Löschen:", e, file=sys.stderr)
    return tgt

def make_thumb(path: str, size: Tuple[int,int]=(160,90)) -> QtGui.QPixmap:
    try:
        from PIL import Image
        img = Image.open(path)
        img.thumbnail(size)
        if img.mode != "RGBA": img = img.convert("RGBA")
        data = img.tobytes("raw", "RGBA")
        qimg = QtGui.QImage(data, img.size[0], img.size[1], QtGui.QImage.Format_RGBA8888)
        return QtGui.QPixmap.fromImage(qimg)
    except Exception:
        pix = QtGui.QPixmap(size[0], size[1]); pix.fill(Qt.gray); return pix

def build_out_name(audio_path: str, out_dir: Path) -> str:
    return str(out_dir / f"{Path(audio_path).stem}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.mp4")

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
        if not self.image_path or not self.audio_path:
            self.valid=False; self.validation_msg="Bild oder Audio fehlt"; return
        ip, ap = Path(self.image_path), Path(self.audio_path)
        if not ip.exists():
            self.valid=False; self.validation_msg=f"Bild fehlt: {ip}"; return
        if not ap.exists():
            self.valid=False; self.validation_msg=f"Audio fehlt: {ap}"; return
        if not ip.is_dir() and ip.suffix.lower() not in (".jpg",".jpeg",".png",".bmp",".webp",".mp4",".mkv",".avi",".mov"):
            self.valid=False; self.validation_msg="Ungültiges Bild/Video"; return
        if ap.suffix.lower() not in (".mp3",".wav",".flac",".m4a",".aac"):
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
    def run(self):
        total = len(self.pairs)
        for i, item in enumerate(self.pairs):
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
                            f.write(f"file '{im}'\n")
                            f.write(f"duration {per}\n")
                        f.write(f"file '{imgs[-1]}'\n")
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
                else:
                    item.status="FERTIG"; item.progress=100.0
                    self.row_progress.emit(i,100.0); self.log.emit(f"Fertig: {item.output}")
            except Exception as e:
                item.status="FEHLER"; self.row_error.emit(i,str(e))
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
        elif act==act_fav:
            self.add_to_fav.emit(path)
            self.window()._log(f"Zu Favoriten: {path}")
        e.accept()

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
        e.accept()


class HelpPane(QtWidgets.QTextBrowser):
    def __init__(self):
        super().__init__()
        self.setOpenExternalLinks(True)
        self.setHtml(self._html())
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
            "</ul>"
        )

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

def _create_panel_grid(rows: int = 3, cols: int = 3) -> QtWidgets.QWidget:
    """Erzeugt ein flexibles Raster mit gleich großen Feldern."""
    grid_widget = QtWidgets.QWidget()
    grid = QtWidgets.QGridLayout(grid_widget)
    grid.setSpacing(5)
    for r in range(rows):
        grid.setRowStretch(r, 1)
        for c in range(cols):
            grid.setColumnStretch(c, 1)
            panel = QtWidgets.QGroupBox(f"Panel {r*cols + c + 1}")
            lay = QtWidgets.QVBoxLayout(panel)
            lbl = QtWidgets.QLabel(f"Inhalt {r*cols + c + 1}")
            lbl.setAlignment(Qt.AlignCenter)
            lay.addWidget(lbl)
            grid.addWidget(panel, r, c)
    return grid_widget

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
        self.setMinimumSize(800, 600)

        self.settings = QtCore.QSettings("Provoware", "VideoBatchTool")
        self._font_size = self.settings.value("ui/font_size", 11, int)
        self.debug_mode = self.settings.value("ui/debug", False, bool)
        logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)

        sys.excepthook = self._global_exception

        self.pairs: List[PairItem] = []
        self.model = PairTableModel(self.pairs)

        ff_ok = check_ffmpeg()
        self.dashboard = InfoDashboard(); self.dashboard.set_env(ff_ok, True)
        if not ff_ok:
            QtWidgets.QMessageBox.warning(self, "FFmpeg fehlt", "Bitte FFmpeg installieren, sonst kann kein Video erzeugt werden.")

        self.image_list = ImageListWidget("Bilder", (".jpg",".jpeg",".png",".bmp",".webp"))
        self.audio_list = DropListWidget("Audios", (".mp3",".wav",".flac",".m4a",".aac"))
        self.favorite_list = FavoriteListWidget("Favoriten", (".jpg",".jpeg",".png",".bmp",".webp"))
        self.image_list.add_to_fav.connect(self._add_to_favorites)
        self.favorite_list.use_fav.connect(self._use_favorite)
        self.favorite_list.removed.connect(lambda p: self._log(f"Favorit entfernt: {p}"))
        self.image_list.files_dropped.connect(self._on_images_added)
        self.audio_list.files_dropped.connect(self._on_audios_added)

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
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

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
        self.preset_combo  = QtWidgets.QComboBox(); self.preset_combo.addItems(
            ["ultrafast","superfast","veryfast","faster","fast","medium","slow","slower","veryslow"])
        self.preset_combo.setCurrentText(self.settings.value("encode/preset","ultrafast",str))
        self.width_spin    = QtWidgets.QSpinBox(); self.width_spin.setRange(16,7680); self.width_spin.setValue(self.settings.value("encode/width",1920,int))
        self.height_spin   = QtWidgets.QSpinBox(); self.height_spin.setRange(16,4320); self.height_spin.setValue(self.settings.value("encode/height",1080,int))
        self.abitrate_edit = QtWidgets.QLineEdit(self.settings.value("encode/abitrate","192k",str))
        self.abitrate_edit.setPlaceholderText("z.B. 192k")
        self.mode_combo   = QtWidgets.QComboBox();
        self.mode_combo.addItems(["Standard","Slideshow","Video + Audio","Mehrere Audios, 1 Bild"])
        self.mode_combo.setToolTip("Verarbeitungsmodus wählen")
        self.mode_combo.setCurrentText(self.settings.value("encode/mode","Standard",str))
        self.clear_after   = QtWidgets.QCheckBox("Nach Fertigstellung Listen leeren")
        self.clear_after.setChecked(self.settings.value("ui/clear_after", False, bool))

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
        form.addRow("", self.clear_after)

        settings_box = QtWidgets.QGroupBox("Einstellungen")
        settings_box.setLayout(form)

        self.settings_widget = settings_box

        table_box = QtWidgets.QGroupBox("Paare")
        tb_lay = QtWidgets.QVBoxLayout(table_box); tb_lay.addWidget(self.table)

        help_box = QtWidgets.QGroupBox("Hilfe")
        hb_lay = QtWidgets.QVBoxLayout(help_box); hb_lay.addWidget(self.help_pane)
        self.help_box = help_box

        left_tabs = QtWidgets.QTabWidget()
        left_tabs.addTab(pool_box, "Dateien")
        left_tabs.addTab(self.settings_widget, "Einstellungen")
        self.sidebar.setWidget(left_tabs)

        panel_grid = _create_panel_grid()

        self.progress_total = QtWidgets.QProgressBar(); self.progress_total.setFormat("%p% gesamt")
        self.progress_total.setAccessibleName("Gesamtfortschritt")
        self.progress_total.setAccessibleDescription("Fortschritt aller Aufgaben")
        self.log_edit = QtWidgets.QPlainTextEdit(); self.log_edit.setReadOnly(True); self.log_edit.setMaximumBlockCount(5000)
        self.log_edit.setAccessibleName("Protokoll")
        self.log_edit.setAccessibleDescription("Fortlaufende Meldungen des Programms")

        self.log_box = QtWidgets.QGroupBox("Protokoll")
        bl = QtWidgets.QVBoxLayout(self.log_box)
        bl.addWidget(self.progress_total)
        bl.addWidget(self.log_edit)

        # Log-Bereich flexibel einteilbar
        main_splitter = QtWidgets.QSplitter(Qt.Vertical)
        main_splitter.addWidget(panel_grid)
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

        self.btn_add_images.setToolTip("Bilder (Fotos) auswählen")
        self.btn_add_audios.setToolTip("Audiodateien auswählen")
        self.btn_auto_pair.setToolTip("Bilder und Audios automatisch koppeln")
        self.btn_clear.setToolTip("Listen komplett leeren")
        self.btn_undo.setToolTip("Letzte Änderung rückgängig machen")
        self.btn_save.setToolTip("Aktuellen Stand speichern")
        self.btn_load.setToolTip("Gespeichertes Projekt laden")
        self.btn_encode.setToolTip("Encoding starten")
        self.btn_stop.setToolTip("Aktuellen Vorgang abbrechen")

        self.btn_encode.setStyleSheet("font-size:14pt;font-weight:bold;background:#005BBB;color:white;padding:4px 10px;")

        top_buttons = QtWidgets.QGridLayout()
        top_buttons.setSpacing(4)
        top_buttons.setContentsMargins(4, 4, 4, 4)
        btn_defs = [
            (self.btn_add_images, "Bilder oder Ordner auswählen"),
            (self.btn_add_audios, "Audiodateien hinzufügen"),
            (self.btn_auto_pair, "Dateien automatisch koppeln"),
            (self.btn_clear, "Listen komplett leeren"),
            (self.btn_undo, "Letzten Schritt rückgängig"),
            (self.btn_save, "Projekt auf Platte sichern"),
            (self.btn_load, "Gespeichertes Projekt laden"),
            (self.btn_encode, "Videos jetzt erstellen"),
            (self.btn_stop, "Laufenden Vorgang abbrechen"),
        ]
        for i, (btn, tip) in enumerate(btn_defs):
            row, col = divmod(i, 4)
            top_buttons.addWidget(self._wrap_button(btn, tip), row, col)
        for i in range(4):
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
        self.table.doubleClicked.connect(self._show_statusbar_path)
        self.btn_out_open.clicked.connect(self._open_out_dir)

        self._set_font(self._font_size)
        self._apply_theme(self.settings.value("ui/theme", "Modern"))
        self.restoreGeometry(self.settings.value("ui/geometry", b"", bytes))
        self.restoreState(self.settings.value("ui/window_state", b"", bytes))
        QtWidgets.QShortcut(QtGui.QKeySequence("F1"), self).activated.connect(
            self._show_help_window
        )

    # ----- UI helpers -----
    def _build_menus(self):
        menubar = self.menuBar()

        m_datei = menubar.addMenu("Datei")
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
        m_hilfe.addAction(act_doc)
        m_hilfe.addAction(act_log)
        m_hilfe.addAction(act_help)

    def _change_font(self, delta:int):
        self._set_font(self._font_size + delta)

    def _set_font(self, size:int):
        size = max(8, min(32, size))
        self._font_size = size
        self._apply_font()
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
        path = self.out_dir_edit.text()
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
        self._log(f"Ausgabeordner geöffnet: {path}")

    def _open_readme(self):
        path = str(Path('README.md').resolve())
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
        self._log("README geöffnet")

    def _open_logfile(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(LOG_FILE)))
        self._log("Logdatei geöffnet")

    def _show_help_window(self):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Kurzanleitung")
        layout = QtWidgets.QVBoxLayout(dlg)
        layout.addWidget(HelpPane())
        dlg.resize(400, 300)
        dlg.exec()
        self._log("Hilfefenster geöffnet")

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

    def _debug(self, msg:str):
        self._log(f"DEBUG: {msg}", logging.DEBUG)

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

    # ----- file actions -----
    def _pick_images(self):
        mode=self.mode_combo.currentText()
        if mode=="Slideshow":
            d=QtWidgets.QFileDialog.getExistingDirectory(self,"Ordner mit Bildern wählen",str(Path.cwd()))
            if d: self._on_images_added([d])
        else:
            files,_=QtWidgets.QFileDialog.getOpenFileNames(self,"Bilder wählen",str(Path.cwd()),
                                                          "Bilder (*.jpg *.jpeg *.png *.bmp *.webp *.mp4 *.mkv *.avi *.mov)")
            if files: self._on_images_added(files)
    def _pick_audios(self):
        files,_=QtWidgets.QFileDialog.getOpenFileNames(self,"Audios wählen",str(Path.cwd()),
                                                       "Audio (*.mp3 *.wav *.flac *.m4a *.aac)")
        if files: self._on_audios_added(files)

    def _on_images_added(self, files: List[str]):
        self._push_history()
        for f in files:
            self.image_list.add_files([f])
            self.model.add_pairs([PairItem(f)])
            self._debug(f"Bild hinzugefügt: {f}")
        self._update_counts()
        self._resize_columns()
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
        self._log("Listen geleert")

    def _undo_last(self):
        if not self._history: return
        last=self._history.pop()
        self.model.clear(); self.model.add_pairs(last)
        self._update_counts()
        self._resize_columns()
        self._log("Rückgängig ausgeführt")

    # ----- save / load -----
    def _save_project(self):
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,"Projekt speichern",str(Path.cwd()/ "projekt.json"),"JSON (*.json)")
        if not path: return
        data={"pairs":[{"image":p.image_path,"audio":p.audio_path,"output":p.output} for p in self.pairs],
              "settings":self._gather_settings()}
        try:
            Path(path).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Fehler beim Speichern", str(e))
            self._log(f"Fehler beim Speichern: {e}")
            return
        self._log(f"Projekt gespeichert: {path}")

    def _load_project(self):
        path,_ = QtWidgets.QFileDialog.getOpenFileName(self, "Projekt laden", str(Path.cwd()), "JSON (*.json)")
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Fehler beim Laden", str(e))
            self._log(f"Fehler beim Laden: {e}")
            return
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
        self._log(f"Projekt geladen: {path}")

    # ----- encode -----
    def _gather_settings(self)->Dict[str,Any]:
        return {"out_dir": self.out_dir_edit.text().strip(),
                "crf": self.crf_spin.value(),
                "preset": self.preset_combo.currentText(),
                "width": self.width_spin.value(),
                "height": self.height_spin.value(),
                "abitrate": self.abitrate_edit.text().strip() or "192k",
                "mode": self.mode_combo.currentText()}

    def _start_encode(self):
        if not self.pairs:
            QtWidgets.QMessageBox.information(
                self,
                "Keine Paare",
                "Bitte zuerst Bilder und Audios hinzufügen.",
            )
            self._log("Encoding abgebrochen: keine Paare")
            return
        if any(p.audio_path is None for p in self.pairs):
            QtWidgets.QMessageBox.warning(self,"Fehlende Audios","Nicht alle Bilder haben ein Audio."); return
        for p in self.pairs: p.validate()
        invalid=[p for p in self.pairs if not p.valid]
        if invalid:
            QtWidgets.QMessageBox.critical(self,"Validierungsfehler",invalid[0].validation_msg); return
        out_dir = Path(self.out_dir_edit.text().strip())
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            test_file = out_dir/".write_test"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ordnerproblem", str(e))
            self._log(f"Encoding abgebrochen: Ordnerproblem ({e})")
            return
        self.btn_encode.setEnabled(False); self.btn_stop.setEnabled(True)
        self.progress_total.setValue(0); self.dashboard.set_progress(0); self._log("Starte Encoding …")
        self.worker = EncodeWorker(self.pairs, self._gather_settings(), self.copy_only)
        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.row_progress.connect(self._on_row_progress)
        self.worker.overall_progress.connect(self._on_overall_progress)
        self.worker.row_error.connect(self._on_row_error)
        self.worker.log.connect(self._log)
        self.worker.finished.connect(self._encode_finished)
        self.thread.start()

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
        self._log(f"Fehler in Zeile {row+1}: {msg}")
        if 0<=row<len(self.pairs):
            self.pairs[row].status="FEHLER"
            idx=self.model.index(row,7); self.model.dataChanged.emit(idx,idx)
        self._update_counts()

    def _encode_finished(self):
        self.btn_encode.setEnabled(True); self.btn_stop.setEnabled(False)
        self.progress_total.setValue(100); self.dashboard.set_progress(100)
        self._log("Alle Jobs abgeschlossen.")
        if self.thread:
            self.thread.quit(); self.thread.wait()
        self.thread=None; self.worker=None
        self._update_counts()
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

    def _global_exception(self, etype, value, tb):
        import traceback
        msg = "".join(traceback.format_exception(etype, value, tb))
        self._log(msg, logging.ERROR)
        short = msg if len(msg) < 1000 else msg[:1000] + "\n...\nSiehe Logdatei für Details."
        QtWidgets.QMessageBox.critical(self, "Unerwarteter Fehler", short)

    def _resize_columns(self):
        header = self.table.horizontalHeader()
        header.resizeSections(QHeaderView.ResizeToContents)

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
        s = self._gather_settings()
        self.settings.setValue("encode/out_dir", s["out_dir"])
        self.settings.setValue("encode/crf", s["crf"])
        self.settings.setValue("encode/preset", s["preset"])
        self.settings.setValue("encode/width", s["width"])
        self.settings.setValue("encode/height", s["height"])
        self.settings.setValue("encode/abitrate", s["abitrate"])
        self.settings.setValue("encode/mode", s["mode"])
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
