from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
from typing import Any

from videobatch_extra import cli_slideshow, cli_video


def _run_job(job: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    mode = job.get("mode", "video")
    source = job.get("source")
    audio = job.get("audio")
    if not source or not audio:
        return {"ok": False, "error": "source/audio fehlt", "job": job}

    if mode == "slideshow":
        code = cli_slideshow(str(source), str(audio), str(out_dir))
    else:
        code = cli_video(str(source), str(audio), str(out_dir))
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
    return parser


def main() -> int:
    args = build_parser().parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    jobs = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    if not isinstance(jobs, list):
        print("Manifest muss eine JSON-Liste sein")
        return 2

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(args.threads, 1)) as pool:
        future_map = {pool.submit(_run_job, job, out_dir): job for job in jobs}
        for future in as_completed(future_map):
            result = future.result()
            results.append(result)
            state = "OK" if result.get("ok") else "FEHLER"
            print(f"[{state}] {result.get('job')}")

    metadata = {
        "jobs": len(jobs),
        "ok": sum(1 for r in results if r.get("ok")),
        "failed": sum(1 for r in results if not r.get("ok")),
        "results": results,
    }
    meta_path = Path(args.metadata_out)
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Metadaten exportiert: {meta_path}")

    return 0 if metadata["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
