from __future__ import annotations

import argparse
from pathlib import Path

from videobatch_extra import (
    cli_multi_audio,
    cli_single,
    cli_slideshow,
    cli_video,
)


def _validate_paths(items: list[str], label: str) -> None:
    missing = [item for item in items if not Path(item).exists()]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"{label}: folgende Pfade fehlen: {joined}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verbesserte CLI mit klaren Parametern und Validierung"
    )
    parser.add_argument(
        "--mode",
        choices=["single", "video", "multi-audio", "slideshow"],
        required=True,
    )
    parser.add_argument("--img", nargs="+", required=True)
    parser.add_argument("--aud", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--crf", type=int, default=23)
    parser.add_argument("--preset", default="ultrafast")
    parser.add_argument("--abitrate", default="192k")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        _validate_paths(args.img, "Bilder/Video")
        _validate_paths(args.aud, "Audio")
        Path(args.out).mkdir(parents=True, exist_ok=True)
    except ValueError as exc:
        print(f"Fehlerhafte Eingabe: {exc}")
        return 2

    if args.verbose:
        print("Verbose: Starte Verarbeitung mit erweiterten Meldungen")
        print(
            f"Modus={args.mode}, Auflösung={args.width}x{args.height}, "
            f"CRF={args.crf}, Preset={args.preset}"
        )

    if args.mode == "single":
        return cli_single(
            args.img,
            args.aud,
            args.out,
            args.width,
            args.height,
            args.crf,
            args.preset,
            args.abitrate,
        )
    if args.mode == "multi-audio":
        return cli_multi_audio(
            args.img[0],
            args.aud,
            args.out,
            args.width,
            args.height,
            args.crf,
            args.preset,
            args.abitrate,
        )
    if args.mode == "video":
        return cli_video(
            args.img[0],
            args.aud[0],
            args.out,
            args.crf,
            args.preset,
            args.abitrate,
        )
    return cli_slideshow(
        args.img[0],
        args.aud[0],
        args.out,
        args.width,
        args.height,
        args.crf,
        args.preset,
        args.abitrate,
    )


if __name__ == "__main__":
    raise SystemExit(main())
