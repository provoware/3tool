from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from subprocess import CompletedProcess, PIPE
from typing import List

import ffmpeg

from .config import cfg


def human_time(seconds: float) -> str:
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return (
        f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        if hours
        else f"{minutes:02d}:{seconds:02d}"
    )


def build_out_name(audio: str, out_dir: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return out_dir / f"{Path(audio).stem}_{stamp}.mp4"


def probe_duration(path: str) -> float:
    try:
        pr = ffmpeg.probe(path)
        fmt = pr.get("format", {})
        if "duration" in fmt:
            return float(fmt["duration"])
        for st in pr.get("streams", []):
            if st.get("codec_type") == "audio":
                return float(st.get("duration", 0) or 0)
    except Exception as e:
        print("Fehler beim Prüfen der Dauer:", e, file=sys.stderr)
    return 0.0


def run_ffmpeg(cmd: List[str]) -> CompletedProcess[str]:
    if cfg.debug:
        print("Starte:", " ".join(cmd))
    try:
        res = subprocess.run(cmd, stdout=PIPE, stderr=PIPE, text=True)
    except FileNotFoundError:
        print("FFmpeg nicht gefunden. Bitte installieren.", file=sys.stderr)
        return CompletedProcess(cmd, 1, "", "ffmpeg fehlt")
    if cfg.debug and res.stderr:
        print(res.stderr)
    return res
