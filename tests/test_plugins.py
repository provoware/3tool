from pathlib import Path

from core.plugins import PluginManager


def test_plugin_manager_runs_before_encode_hook(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "demo.py").write_text(
        "def before_encode(payload):\n"
        "    cmd = payload.get('command', []) + ['-metadata', 'plugin=test']\n"
        "    payload['command'] = cmd\n"
        "    return payload\n",
        encoding="utf-8",
    )

    manager = PluginManager(plugin_dir)
    manager.load()
    result = manager.run_hook("before_encode", {"command": ["ffmpeg"]})

    assert result["command"][-1] == "plugin=test"
