from __future__ import annotations

import app
import start_gui
import videobatch_launcher


def test_app_smoke_gui_uses_bootstrap(monkeypatch) -> None:
    calls = {"bootstrap": 0, "entry": 0}

    monkeypatch.setattr(
        app,
        "run_bootstrap",
        lambda *_args, **_kwargs: calls.__setitem__("bootstrap", calls["bootstrap"] + 1),
    )
    monkeypatch.setattr(
        app,
        "_import_callable",
        lambda _module, _func: lambda: calls.__setitem__("entry", calls["entry"] + 1),
    )

    result = app.main(["--mode", "gui", "--smoke-only"])

    assert result == 0
    assert calls["bootstrap"] == 1
    assert calls["entry"] == 0


def test_app_cli_mode_calls_videobatch_extra_main(monkeypatch) -> None:
    calls = {"bootstrap": 0, "entry": 0}

    monkeypatch.setattr(
        app,
        "run_bootstrap",
        lambda *_args, **_kwargs: calls.__setitem__("bootstrap", calls["bootstrap"] + 1),
    )
    monkeypatch.setattr(
        app,
        "_import_callable",
        lambda _module, _func: lambda: calls.__setitem__("entry", calls["entry"] + 1),
    )

    result = app.main(["--mode", "cli", "--smoke-only"])

    assert result == 0
    assert calls["bootstrap"] == 1
    assert calls["entry"] == 0


def test_legacy_start_gui_forwards_to_primary(monkeypatch) -> None:
    monkeypatch.setattr(
        start_gui,
        "parse_args",
        lambda: type(
            "Args", (), {"debug": True, "simple_mode": True, "release_check": False, "auto_repair": False}
        )(),
    )
    captured: dict[str, list[str]] = {"args": []}

    def _fake_primary(argv: list[str]) -> int:
        captured["args"] = argv
        return 0

    monkeypatch.setattr("app.main", _fake_primary)

    result = start_gui.main()

    assert result == 0
    assert captured["args"] == ["--mode", "gui", "--debug", "--simple-mode"]


def test_legacy_launcher_forwards_to_primary(monkeypatch) -> None:
    monkeypatch.delenv("VT_DEBUG", raising=False)
    captured: dict[str, list[str]] = {"args": []}

    def _fake_primary(argv: list[str]) -> int:
        captured["args"] = argv
        return 0

    monkeypatch.setattr("app.main", _fake_primary)

    result = videobatch_launcher.main()

    assert result == 0
    assert captured["args"] == ["--mode", "gui"]
