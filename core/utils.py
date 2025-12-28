from __future__ import annotations

import re
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


def _sanitize_filename(name: str) -> str:
    name = name.strip()
    if not name:
        return "output.mp4"
    name = name.replace("/", "_").replace("\\", "_")
    name = re.sub(r'[<>:"|?*]', "_", name)
    return name or "output.mp4"


def build_out_name(
    audio: str,
    out_dir: Path,
    template: str | None = None,
    now: datetime | None = None,
) -> Path:
    now = now or datetime.now()
    stamp = now.strftime("%Y%m%d-%H%M%S")
    audio_stem = Path(audio).stem if audio else "audio"
    values = {
        "audio_stem": audio_stem or "audio",
        "date": now.strftime("%Y%m%d"),
        "time": now.strftime("%H%M%S"),
        "stamp": stamp,
    }
    template = (template or "{audio_stem}_{stamp}.mp4").strip()
    try:
        filename = template.format(**values)
    except KeyError as exc:
        raise ValueError(f"Unbekannter Platzhalter: {exc.args[0]}") from exc
    filename = _sanitize_filename(filename)
    if not filename.lower().endswith(".mp4"):
        filename = f"{filename}.mp4"
    return out_dir / filename


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
