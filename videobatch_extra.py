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
import random
import re
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from core import __version__
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


_NAT_SORT_RE = re.compile(r"(\d+)")


def _normalize_color(color: str) -> str:
    value = color.strip()
    if value.startswith("#"):
        value = "0x" + value[1:]
    return value


def _natural_key(value: str) -> List[object]:
    parts = _NAT_SORT_RE.split(value)
    key: List[object] = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part.lower())
    return key


def _escape_for_concat(path: Path) -> str:
    escaped = str(path).replace("'", r"'\\''")
    return f"'{escaped}'"


def _collect_images(
    directory: Path,
    extensions: Sequence[str],
    order: str,
    reverse: bool,
    shuffle: bool,
) -> Tuple[List[Path], int]:
    images: List[Path] = []
    for pattern in extensions:
        images.extend(directory.glob(pattern))
    if not images:
        return [], 0
    # Deduplicate while keeping deterministic ordering before shuffle
    unique: dict[str, Path] = {}
    for img in images:
        unique[str(img)] = img
    duplicates = len(images) - len(unique)
    images = list(unique.values())

    if order == "mtime":
        def mtime_key(p: Path) -> tuple[float, str]:
            try:
                return (p.stat().st_mtime, p.name.lower())
            except OSError:
                return (0.0, p.name.lower())

        images.sort(key=mtime_key)
    elif order == "name":
        images.sort(key=lambda p: p.name.lower())
    else:  # natural
        images.sort(key=lambda p: _natural_key(p.name))

    if reverse:
        images.reverse()
    if shuffle:
        random.shuffle(images)
    return images, duplicates


def _build_video_filters(
    width: int,
    height: int,
    background: str,
    fit_mode: str,
) -> List[str]:
    if fit_mode == "cover":
        return [
            "scale="
            f"{width}:{height}:force_original_aspect_ratio=increase",
            f"crop={width}:{height}",
        ]
    return [
        "scale="
        f"{width}:{height}:force_original_aspect_ratio=decrease",
        "pad="
        f"{width}:{height}:(ow-iw)/2:(oh-ih)/2:color={_normalize_color(background)}",
    ]


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
    image_duration: Optional[float] = None,
    min_image_duration: float = 0.3,
    framerate: int = 30,
    background: str = "black",
    video_filter: Optional[str] = None,
    audio_fade: float = 0.0,
    audio_filter: Optional[str] = None,
    order: str = "natural",
    reverse: bool = False,
    shuffle: bool = False,
    fit_mode: str = "contain",
    extensions: Optional[Sequence[str]] = None,
    video_codec: str = "libx264",
    audio_codec: str = "aac",
    pix_fmt: Optional[str] = "yuv420p",
    movflags: Optional[str] = "+faststart",
    video_bitrate: Optional[str] = None,
    video_tune: Optional[str] = "stillimage",
) -> int:
    d = Path(img_dir)
    audio_path = Path(audio)
    errors: List[str] = []
    if not d.exists():
        errors.append("Bildordner fehlt")
    elif not d.is_dir():
        errors.append("Bildpfad ist kein Ordner")
    if not audio_path.exists():
        errors.append("Audiodatei fehlt")
    elif not audio_path.is_file():
        errors.append("Audiopfad ist keine Datei")
    if width <= 0:
        errors.append("Breite muss > 0 sein")
    if height <= 0:
        errors.append("Höhe muss > 0 sein")
    if min_image_duration <= 0:
        errors.append("minimale Bilddauer muss > 0 sein")
    if framerate <= 0:
        errors.append("Framerate muss > 0 sein")
    if audio_fade < 0:
        errors.append("Audio-Fade darf nicht negativ sein")
    if pix_fmt is not None and not pix_fmt.strip():
        errors.append("pix_fmt darf nicht leer sein")
    if movflags is not None and not movflags.strip():
        errors.append("movflags darf nicht leer sein")
    if not video_codec.strip():
        errors.append("Video-Codec darf nicht leer sein")
    if not audio_codec.strip():
        errors.append("Audio-Codec darf nicht leer sein")
    if errors:
        print("Fehlerhafte Eingabe:")
        for err in errors:
            print(" -", err)
        return 1
    img_ext = extensions or ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp")
    images, duplicates = _collect_images(d, img_ext, order, reverse, shuffle)
    if not images:
        print("Keine Bilder gefunden")
        return 1
    if image_duration is not None and image_duration <= 0:
        print("Bilddauer muss positiv sein")
        return 1
    fps = max(framerate, 1)
    dur = probe_duration(str(audio_path))
    min_per = max(min_image_duration, 1.0 / fps)
    if image_duration is not None and image_duration > 0:
        per = max(image_duration, min_per)
    elif dur:
        per = max(dur / len(images), min_per)
    else:
        per = max(2.0, min_per)
    if image_duration is not None and image_duration < min_per:
        print(
            "Hinweis: Gewünschte Bilddauer war kürzer als erlaubt – Wert wurde angehoben",
        )
    fade_used = 0.0
    if audio_fade > 0 and dur:
        fade_used = min(audio_fade, max(dur - 0.1, 0) / 2)
        if fade_used <= 0:
            print("Hinweis: Audio ist zu kurz für einen Fade-Effekt")
        elif fade_used < audio_fade:
            print(
                "Hinweis: Fade-Dauer wurde gekürzt, damit Anfang und Ende passen",
            )
    if dur == 0:
        print(
            "Hinweis: Audiolänge konnte nicht ermittelt werden – Standardwerte werden genutzt",
        )
    total_video = per * len(images)
    if dur and abs(total_video - dur) > 1.0:
        diff = dur - total_video
        if diff > 0:
            print(
                f"Hinweis: Audio ist {diff:.1f}s länger als die Slideshow – Ende wird automatisch gekürzt",
            )
        else:
            print(
                f"Hinweis: Slideshow ist {-diff:.1f}s länger als das Audio – Video stoppt beim Audio-Ende",
            )
    print("Slideshow-Check:")
    print(f" - Bilder insgesamt: {len(images)}")
    if duplicates:
        print(f" - Duplikate verworfen: {duplicates}")
    print(f" - Bilddauer effektiv: {per:.2f}s")
    print(f" - Framerate: {fps} fps")
    print(f" - Videoauflösung: {width}x{height}")
    if video_filter:
        print(" - Zusätzlicher Video-Filter aktiv")
    if audio_filter:
        print(" - Zusätzlicher Audio-Filter aktiv")
    if fade_used > 0:
        print(f" - Audio-Fade in/out: {fade_used:.2f}s")
    if shuffle:
        print(" - Bilder werden gemischt")
    if reverse:
        print(" - Reihenfolge wird umgedreht")
    if video_bitrate:
        print(f" - Videobitrate gesetzt: {video_bitrate}")
        print("   Hinweis: Kombination aus Bitrate und CRF kann zu FFmpeg-Warnungen führen")
    with tempfile.NamedTemporaryFile(
        delete=False, mode="w", suffix=".txt"
    ) as f:
        for img in images:
            f.write(f"file {_escape_for_concat(img)}\n")
            f.write(f"duration {per}\n")
        f.write(f"file {_escape_for_concat(images[-1])}\n")
        list_path = f.name
    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)
    out_file = build_out_name(audio, out_dir_p)
    video_filters = _build_video_filters(width, height, background, fit_mode)
    if video_filter:
        video_filters.append(video_filter)
    audio_filters: List[str] = []
    if fade_used > 0:
        audio_filters.append(f"afade=in:st=0:d={fade_used:.3f}")
        out_start = max(dur - fade_used, 0)
        audio_filters.append(f"afade=out:st={out_start:.3f}:d={fade_used:.3f}")
    if audio_filter:
        audio_filters.append(audio_filter)
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
        video_codec,
        "-vf",
        ",".join(video_filters),
        "-r",
        str(fps),
    ]
    if video_tune and video_tune.lower() != "none":
        cmd += ["-tune", video_tune]
    if video_bitrate:
        cmd += ["-b:v", video_bitrate]
    if pix_fmt and pix_fmt.lower() != "none":
        cmd += ["-pix_fmt", pix_fmt]
    cmd += [
        "-c:a",
        audio_codec,
        "-b:a",
        abitrate,
        "-shortest",
        "-preset",
        preset,
        "-crf",
        str(crf),
    ]
    if movflags and movflags.lower() != "none":
        cmd += ["-movflags", movflags]
    if audio_filters:
        cmd += ["-af", ",".join(audio_filters)]
    cmd.append(str(out_file))
    try:
        res = run_ffmpeg(cmd)
    finally:
        try:
            os.unlink(list_path)
        except FileNotFoundError:
            pass
    if res.returncode != 0:
        err = res.stderr.strip().splitlines()
        msg = err[-1] if err else "unbekannt"
        print("FFmpeg-Fehler:", msg)
        return 1
    print("Fertig: 1/1")
    print(
        "Nutzerinfo:",
        (
            f"{len(images)} Bilder, {dur:.1f}s Audio, {per:.2f}s pro Bild, "
            f"Modus {fit_mode}, Codec {video_codec}/{audio_codec}"
        ),
    )
    return 0


def run_selftests() -> int:
    assert human_time(65) == "01:05"
    assert _natural_key("bild12.png") > _natural_key("bild3.png")
    assert _build_video_filters(1920, 1080, "#000000", "contain")[1].startswith("pad=")
    assert _build_video_filters(1920, 1080, "#000000", "cover")[1].startswith("crop=")
    with tempfile.TemporaryDirectory() as td:
        out = build_out_name(str(Path(td) / "a.mp3"), Path(td))
        assert out.name.endswith(".mp4")
        assert re.search(r"a_\d{8}-\d{6}\.mp4$", out.name)
    with tempfile.TemporaryDirectory() as td:
        folder = Path(td)
        for name in ["bild1.jpg", "bild2.jpg", "bild10.jpg"]:
            (folder / name).write_bytes(b"")
        images, duplicates = _collect_images(
            folder, ("*.jpg", "*.jpg"), "natural", False, False
        )
        assert [img.name for img in images] == ["bild1.jpg", "bild2.jpg", "bild10.jpg"]
        assert duplicates == 3
    print("Selftests OK")
    return 0


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="VideoBatchTool CLI / Tests")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
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
    parser.add_argument("--image-duration", type=float)
    parser.add_argument("--min-image-duration", type=float, default=0.3)
    parser.add_argument("--framerate", type=int, default=30)
    parser.add_argument("--background", default="black")
    parser.add_argument("--video-filter")
    parser.add_argument("--audio-fade", type=float, default=0.0)
    parser.add_argument("--audio-filter")
    parser.add_argument("--video-codec", default="libx264")
    parser.add_argument("--audio-codec", default="aac")
    parser.add_argument("--pix-fmt", default="yuv420p")
    parser.add_argument("--movflags", default="+faststart")
    parser.add_argument("--video-bitrate")
    parser.add_argument("--video-tune", default="stillimage")
    parser.add_argument(
        "--order",
        choices=["natural", "name", "mtime"],
        default="natural",
    )
    parser.add_argument("--reverse", action="store_true")
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument(
        "--image-fit",
        choices=["contain", "cover"],
        default="contain",
    )
    parser.add_argument(
        "--image-extensions",
        default="*.jpg,*.jpeg,*.png,*.bmp,*.webp",
        help="Komma-Liste mit Globmustern, z.B. '*.jpg,*.png'",
    )
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
        patterns = [p.strip() for p in args.image_extensions.split(",") if p.strip()]
        if not patterns:
            patterns = None
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
                args.image_duration,
                args.min_image_duration,
                args.framerate,
                args.background,
                args.video_filter,
                args.audio_fade,
                args.audio_filter,
                args.order,
                args.reverse,
                args.shuffle,
                args.image_fit,
                patterns,
                args.video_codec,
                args.audio_codec,
                args.pix_fmt,
                args.movflags,
                args.video_bitrate,
                args.video_tune,
            )
        )
    print("GUI starten: python3 videobatch_launcher.py")


if __name__ == "__main__":
    main()
