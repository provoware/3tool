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


def linux_safe_stem(raw_value: str, fallback: str = "wert") -> str:
    value = (raw_value or "").strip().lower()
    if not value:
        return fallback
    value = value.replace(" ", "_")
    value = re.sub(r"[^a-z0-9._-]", "_", value)
    value = re.sub(r"_+", "_", value)
    value = value.strip("._-")
    return value or fallback


def build_output_name_values(
    audio: str,
    *,
    now: datetime | None = None,
    duration_seconds: float | None = None,
    quality: str | None = None,
    resolution: str | None = None,
    form: str | None = None,
) -> dict[str, str]:
    now = now or datetime.now()
    stamp = now.strftime("%Y%m%d-%H%M%S")
    audio_stem = Path(audio).stem if audio else "audio"
    duration = max(0, int(duration_seconds or 0))
    return {
        "audio_stem": linux_safe_stem(audio_stem or "audio", "audio"),
        "audio_name": linux_safe_stem(audio_stem or "audio", "audio"),
        "date": now.strftime("%Y%m%d"),
        "time": now.strftime("%H%M%S"),
        "stamp": stamp,
        "video_laenge": f"{duration:04d}s",
        "zeitstempel": stamp,
        "qualitaet": linux_safe_stem(quality or "auto", "auto"),
        "abmasse": linux_safe_stem(resolution or "0x0", "0x0"),
        "form": linux_safe_stem(form or "standard", "standard"),
    }


def mark_used_filename(src: Path) -> str:
    stem = linux_safe_stem(src.stem, "datei")
    suffix = src.suffix.lower()
    if not suffix:
        suffix = ".dat"
    return f"{stem}_benutzt{suffix}"


def build_out_name(
    audio: str,
    out_dir: Path,
    template: str | None = None,
    now: datetime | None = None,
    duration_seconds: float | None = None,
    quality: str | None = None,
    resolution: str | None = None,
    form: str | None = None,
) -> Path:
    values = build_output_name_values(
        audio,
        now=now,
        duration_seconds=duration_seconds,
        quality=quality,
        resolution=resolution,
        form=form,
    )
    template = (
        template
        or "{audio_name}_{video_laenge}_{zeitstempel}_{qualitaet}_{abmasse}_{form}.mp4"
    ).strip()
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
