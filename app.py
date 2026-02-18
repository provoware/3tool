from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Callable

from core.bootstrap import BootstrapError, run_bootstrap
from core.config import apply_simple_mode_defaults, cfg

PROJECT_ROOT = Path(__file__).resolve().parent
REQUIRED_FILES = ("videobatch_gui.py", "videobatch_extra.py")


def _import_callable(module_name: str, callable_name: str) -> Callable[[], int | None]:
    root = str(PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    module = importlib.import_module(module_name)
    target = getattr(module, callable_name, None)
    if not callable(target):
        raise BootstrapError(
            f"Startziel fehlt: {module_name}.{callable_name} ist nicht aufrufbar."
        )
    return target


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Primaerer Startpfad fuer VideoBatchTool (GUI/CLI)"
    )
    parser.add_argument(
        "--mode",
        choices=("gui", "cli"),
        default="gui",
        help="Startmodus: gui (Standard) oder cli.",
    )
    parser.add_argument("--debug", action="store_true", help="Debug-Logging aktivieren.")
    parser.add_argument(
        "--simple-mode",
        action="store_true",
        help="Ressourcenschonende Defaults (720p, CRF 24, veryfast).",
    )
    parser.add_argument(
        "--smoke-only",
        action="store_true",
        help="Nur Bootstrap ausfuehren, danach ohne GUI/CLI-Job mit Code 0 beenden.",
    )
    return parser.parse_args(argv)


def run_mode(mode: str, debug: bool, simple_mode: bool, smoke_only: bool) -> int:
    if simple_mode:
        apply_simple_mode_defaults()
        cfg.simple_mode = True
    run_bootstrap(PROJECT_ROOT, REQUIRED_FILES, debug)
    if smoke_only:
        return 0

    if mode == "gui":
        target = _import_callable("start_gui", "run_from_primary_entry")
        result = target()
        return 0 if result is None else int(result)

    target = _import_callable("videobatch_extra", "main")
    result = target()
    return 0 if result is None else int(result)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg.debug = args.debug
    try:
        return run_mode(args.mode, args.debug, args.simple_mode, args.smoke_only)
    except BootstrapError as exc:
        print(f"❌ {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
