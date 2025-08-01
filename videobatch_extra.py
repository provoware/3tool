# =========================================
# QUICKSTART
# CLI-Encode:
#   python3 videobatch_extra.py --img bild.jpg --aud ton.mp3 --out outdir
# Weitere Modi siehe --mode (single, slideshow, video, multi-audio)
# Selftests:   python3 videobatch_extra.py --selftest
# Edit:        micro videobatch_extra.py
# =========================================

# videobatch_extra.py
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path
from typing import List

from core.config import cfg
from core.utils import build_out_name, human_time, probe_duration, run_ffmpeg


def verify_files(*paths: str) -> bool:
    """Prueft, ob Dateien existieren."""
    ok = True
    for p in paths:
        if not Path(p).exists():
            print(f"Fehlt: {p}")
            ok = False
    return ok


def cli_single(
    images: List[str],
    audios: List[str],
    out_dir: str,
    width: int = 1920,
    height: int = 1080,
    crf: int = 23,
    preset: str = 'ultrafast',
    abitrate: str = '192k',
) -> int:
    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)
    if len(images) != len(audios):
        print('Fehler: Anzahl Bilder != Anzahl Audios')
        return 1
    total = len(images)
    done = 0
    for i, (img, aud) in enumerate(zip(images, audios), 1):
        if not verify_files(img, aud):
            print(f"[{i}/{total}] FEHLT: {img} / {aud}")
            continue
        out_file = build_out_name(aud, out_dir_p)
        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            img,
            "-i",
            aud,
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-vf",
            (
                "scale="
                f"{width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
            ),
            "-c:a",
            "aac",
            "-b:a",
            abitrate,
            "-shortest",
            "-preset",
            preset,
            "-crf",
            str(crf),
            str(out_file),
        ]
        res = run_ffmpeg(cmd)
        if res.returncode == 0:
            done += 1
        else:
            err = res.stderr.strip().splitlines()
            msg = err[-1] if err else "unbekannt"
            print("FFmpeg-Fehler:", msg)
    print(f"Fertig: {done}/{total}")
    return 0


def cli_multi_audio(
    image: str,
    audios: List[str],
    out_dir: str,
    width: int = 1920,
    height: int = 1080,
    crf: int = 23,
    preset: str = "ultrafast",
    abitrate: str = "192k",
) -> int:
    return cli_single(
        [image] * len(audios),
        audios,
        out_dir,
        width,
        height,
        crf,
        preset,
        abitrate,
    )


def cli_video(
    video: str,
    audio: str,
    out_dir: str,
    crf: int = 23,
    preset: str = "ultrafast",
    abitrate: str = "192k",
) -> int:
    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)
    if not verify_files(video, audio):
        return 1
    out_file = build_out_name(audio, out_dir_p)
    vdur = probe_duration(video)
    adur = probe_duration(audio)
    extra = max(0.0, adur - vdur)
    cmd = ["ffmpeg", "-y", "-i", video, "-i", audio]
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
        abitrate,
        "-shortest",
        "-preset",
        preset,
        "-crf",
        str(crf),
        str(out_file),
    ]
    res = run_ffmpeg(cmd)
    if res.returncode != 0:
        err = res.stderr.strip().splitlines()
        msg = err[-1] if err else "unbekannt"
        print("FFmpeg-Fehler:", msg)
        return 1
    print("Fertig: 1/1")
    return 0


def cli_slideshow(
    img_dir: str,
    audio: str,
    out_dir: str,
    width: int = 1920,
    height: int = 1080,
    crf: int = 23,
    preset: str = "ultrafast",
    abitrate: str = "192k",
) -> int:
    d = Path(img_dir)
    if not d.exists() or not verify_files(audio):
        print("Ordner fehlt" if not d.exists() else "Datei fehlt")
        return 1
    images = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp"):
        images.extend(sorted(d.glob(ext)))
    if not images:
        print("Keine Bilder gefunden")
        return 1
    dur = probe_duration(audio)
    per = dur / len(images) if dur else 2
    with tempfile.NamedTemporaryFile(
        delete=False, mode="w", suffix=".txt"
    ) as f:
        for img in images:
            f.write(f"file '{img}'\n")
            f.write(f"duration {per}\n")
        f.write(f"file '{images[-1]}'\n")
        list_path = f.name
    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)
    out_file = build_out_name(audio, out_dir_p)
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
        audio,
        "-c:v",
        "libx264",
        "-vf",
        (
            "scale="
            f"{width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
        ),
        "-c:a",
        "aac",
        "-b:a",
        abitrate,
        "-shortest",
        "-preset",
        preset,
        "-crf",
        str(crf),
        str(out_file),
    ]
    res = run_ffmpeg(cmd)
    os.unlink(list_path)
    if res.returncode != 0:
        err = res.stderr.strip().splitlines()
        msg = err[-1] if err else "unbekannt"
        print("FFmpeg-Fehler:", msg)
        return 1
    print("Fertig: 1/1")
    return 0


def run_selftests() -> int:
    assert human_time(65) == "01:05"
    with tempfile.TemporaryDirectory() as td:
        out = build_out_name(str(Path(td) / "a.mp3"), Path(td))
        assert out.name.endswith(".mp4")
        assert re.search(r"a_\d{8}-\d{6}\.mp4$", out.name)
    print("Selftests OK")
    return 0


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="VideoBatchTool CLI / Tests")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--img", nargs="+")
    parser.add_argument("--aud", nargs="+")
    parser.add_argument("--out", default=".")
    parser.add_argument(
        "--mode",
        choices=["single", "slideshow", "video", "multi-audio"],
        default="single",
    )
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--crf", type=int, default=23)
    parser.add_argument("--preset", default="ultrafast")
    parser.add_argument("--abitrate", default="192k")
    args = parser.parse_args()

    cfg.debug = args.debug

    if args.selftest:
        sys.exit(run_selftests())
    if args.mode == "single" and args.img and args.aud:
        sys.exit(
            cli_single(
                args.img,
                args.aud,
                args.out,
                args.width,
                args.height,
                args.crf,
                args.preset,
                args.abitrate,
            )
        )
    if args.mode == "multi-audio" and args.img and args.aud:
        sys.exit(
            cli_multi_audio(
                args.img[0],
                args.aud,
                args.out,
                args.width,
                args.height,
                args.crf,
                args.preset,
                args.abitrate,
            )
        )
    if args.mode == "video" and args.img and args.aud:
        sys.exit(
            cli_video(
                args.img[0],
                args.aud[0],
                args.out,
                args.crf,
                args.preset,
                args.abitrate,
            )
        )
    if args.mode == "slideshow" and args.img and args.aud:
        sys.exit(
            cli_slideshow(
                args.img[0],
                args.aud[0],
                args.out,
                args.width,
                args.height,
                args.crf,
                args.preset,
                args.abitrate,
            )
        )
    print("GUI starten: python3 videobatch_launcher.py")


if __name__ == "__main__":
    main()
