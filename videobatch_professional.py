from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
from pathlib import Path
from typing import Any

from core.paths import log_dir
from videobatch_extra import cli_slideshow, cli_video


LOGGER = logging.getLogger("videobatch.professional")
VALID_MODES = {"video", "slideshow"}


def _configure_logging(debug: bool, log_file: Path) -> None:
    if not isinstance(log_file, Path):
        raise TypeError("log_file muss ein Path sein")

    log_file.parent.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if debug else logging.INFO
    handlers: list[logging.Handler] = [
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding="utf-8"),
    ]
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )


def _normalize_threads(threads: int) -> int:
    if threads <= 0:
        raise ValueError(
            "threads muss groesser als 0 sein. "
            "Naechster Schritt: --threads 2 setzen."
        )
    return threads


def _load_manifest(path: Path) -> list[dict[str, Any]]:
    if not isinstance(path, Path):
        raise TypeError("manifest path muss ein Path sein")
    if not path.exists() or not path.is_file():
        raise ValueError(
            "Manifest fehlt oder ist keine Datei. "
            "Naechster Schritt: pruefen mit 'ls <manifest.json>'."
        )

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Manifest ist kein gueltiges JSON. "
            "Naechster Schritt: mit einem JSON-Validator pruefen."
        ) from exc

    if not isinstance(data, list):
        raise ValueError("Manifest muss eine JSON-Liste sein")

    normalized: list[dict[str, Any]] = []
    for index, job in enumerate(data):
        if not isinstance(job, dict):
            raise ValueError(f"Job #{index + 1} muss ein JSON-Objekt sein")

        mode = str(job.get("mode", "video")).strip().lower()
        source = str(job.get("source", "")).strip()
        audio = str(job.get("audio", "")).strip()
        if mode not in VALID_MODES:
            raise ValueError(
                f"Job #{index + 1}: mode '{mode}' ist ungueltig. "
                "Erlaubt: video, slideshow."
            )
        if not source or not audio:
            raise ValueError(
                f"Job #{index + 1}: source/audio fehlen. "
                "Naechster Schritt: beide Pfade eintragen."
            )

        normalized.append({"mode": mode, "source": source, "audio": audio})
    return normalized


def _run_job(job: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    mode = str(job.get("mode", "video")).strip().lower()
    source = str(job.get("source", "")).strip()
    audio = str(job.get("audio", "")).strip()
    if not source or not audio:
        return {"ok": False, "error": "source/audio fehlt", "job": job}

    source_path = Path(source)
    audio_path = Path(audio)
    if not source_path.exists():
        return {
            "ok": False,
            "error": f"Quelldatei fehlt: {source_path}",
            "job": job,
        }
    if not audio_path.exists() or not audio_path.is_file():
        return {
            "ok": False,
            "error": f"Audiodatei fehlt/ungueltig: {audio_path}",
            "job": job,
        }

    LOGGER.debug("Starte Job mode=%s source=%s audio=%s", mode, source, audio)

    if mode == "slideshow":
        code = cli_slideshow(str(source), str(audio), str(out_dir))
    elif mode == "video":
        code = cli_video(str(source), str(audio), str(out_dir))
    else:
        return {
            "ok": False,
            "error": f"Ungueltiger Modus: {mode}",
            "job": job,
        }

    LOGGER.debug("Job beendet mode=%s exit_code=%s", mode, code)
    return {"ok": code == 0, "exit_code": code, "job": job}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Professional CLI: Batch-Workflows, Parallelisierung und "
            "JSON-Metadaten-Export"
        )
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--metadata-out", default="batch_metadata.json")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Detailliertes Debug-Protokoll aktivieren",
    )
    parser.add_argument(
        "--log-file",
        default=str(log_dir() / "videobatch_professional.log"),
        help="Pfad zur Log-Datei",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    _configure_logging(args.debug, Path(args.log_file))

    try:
        threads = _normalize_threads(args.threads)
        jobs = _load_manifest(Path(args.manifest))
    except (TypeError, ValueError) as exc:
        print(f"Fehler: {exc}")
        LOGGER.error("Eingabe ungueltig: %s", exc)
        return 2

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info(
        "Batch-Start: jobs=%s threads=%s out=%s", len(jobs), threads, out_dir
    )

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=threads) as pool:
        future_map = {pool.submit(_run_job, job, out_dir): job for job in jobs}
        for future in as_completed(future_map):
            result = future.result()
            results.append(result)
            state = "OK" if result.get("ok") else "FEHLER"
            error_msg = result.get("error")
            suffix = f" | {error_msg}" if error_msg else ""
            print(f"[{state}] {result.get('job')}{suffix}")

    metadata = {
        "jobs": len(jobs),
        "ok": sum(1 for r in results if r.get("ok")),
        "failed": sum(1 for r in results if not r.get("ok")),
        "results": results,
    }
    meta_path = Path(args.metadata_out)
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    LOGGER.info("Metadaten exportiert: %s", meta_path)
    print(f"Metadaten exportiert: {meta_path}")

    return 0 if metadata["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
