from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from typing import Any, Iterable

LOGGER = logging.getLogger("VideoBatchTool.plugins")


class PluginManager:
    """Leichtgewichtiger Hook-Manager fuer Erweiterbarkeit ohne harte Kopplung."""

    def __init__(self, plugin_dir: Path):
        self.plugin_dir = plugin_dir
        self._modules: list[Any] = []

    def load(self) -> None:
        self._modules.clear()
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        for plugin_file in sorted(self.plugin_dir.glob("*.py")):
            if plugin_file.name.startswith("_"):
                continue
            module = self._load_module(plugin_file)
            if module is not None:
                self._modules.append(module)
                LOGGER.info("Plugin geladen: %s", plugin_file.name)

    def _load_module(self, plugin_file: Path) -> Any | None:
        spec = importlib.util.spec_from_file_location(
            f"videobatch_plugin_{plugin_file.stem}",
            plugin_file,
        )
        if spec is None or spec.loader is None:
            LOGGER.warning(
                "Plugin konnte nicht geladen werden: %s", plugin_file
            )
            return None
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            LOGGER.error("Plugin-Fehler beim Laden %s: %s", plugin_file, exc)
            return None
        return module

    def run_hook(
        self,
        hook_name: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        current_payload = dict(payload or {})
        for module in self._modules:
            func = getattr(module, hook_name, None)
            if not callable(func):
                continue
            try:
                maybe = func(current_payload)
                if isinstance(maybe, dict):
                    current_payload = maybe
            except Exception as exc:
                LOGGER.error(
                    "Plugin-Hook %s in %s fehlgeschlagen: %s",
                    hook_name,
                    getattr(module, "__name__", "unbekannt"),
                    exc,
                )
        return current_payload

    @property
    def loaded_plugins(self) -> Iterable[str]:
        for module in self._modules:
            yield getattr(module, "__name__", "unbekannt")
