import unittest
from pathlib import Path

from core import launcher_checks


class LauncherChecksTests(unittest.TestCase):
    def test_python_version_check_has_expected_keys(self):
        result = launcher_checks.check_python_version()
        self.assertEqual(result.key, "python_version")
        self.assertIn("Python", result.title)
        self.assertTrue(result.detail)

    def test_write_permissions_ok_in_current_dir(self):
        self.assertTrue(launcher_checks.write_permissions_ok(Path.cwd()))


def _result_by_key(results, key):
    return next(result for result in results if result.key == key)


def test_run_repairs_offline_skips_install(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher_checks, "has_internet", lambda: False)
    monkeypatch.setattr(launcher_checks, "ensure_venv", lambda: None)
    monkeypatch.setattr(launcher_checks, "ensure_pip", lambda py: True)
    monkeypatch.setattr(launcher_checks, "pip_show", lambda py, pkg: False)
    monkeypatch.setattr(
        launcher_checks, "module_import_ok", lambda py, name: False
    )
    monkeypatch.setattr(launcher_checks.shutil, "which", lambda _: None)
    monkeypatch.setattr(launcher_checks, "write_permissions_ok", lambda _: True)

    results = launcher_checks.run_repairs("python", tmp_path)

    packages = _result_by_key(results, "packages")
    assert not packages.ok
    assert packages.skipped_offline
    assert "Kein Internet" in packages.detail

    ffmpeg = _result_by_key(results, "ffmpeg")
    assert not ffmpeg.ok
    assert ffmpeg.skipped_offline
    assert "Kein Internet" in ffmpeg.detail


def test_run_repairs_installs_missing_packages(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher_checks, "has_internet", lambda: True)
    monkeypatch.setattr(launcher_checks, "ensure_venv", lambda: None)
    monkeypatch.setattr(launcher_checks, "ensure_pip", lambda py: True)
    monkeypatch.setattr(launcher_checks, "pip_show", lambda py, pkg: False)
    monkeypatch.setattr(
        launcher_checks, "module_import_ok", lambda py, name: False
    )
    monkeypatch.setattr(
        launcher_checks.shutil,
        "which",
        lambda name: (
            "/usr/bin/ffmpeg" if name in {"ffmpeg", "ffprobe"} else None
        ),
    )
    monkeypatch.setattr(launcher_checks, "write_permissions_ok", lambda _: True)
    installed = []

    def _pip_install(py, pkgs):
        installed.extend(pkgs)

    monkeypatch.setattr(launcher_checks, "pip_install", _pip_install)

    results = launcher_checks.run_repairs("python", tmp_path)

    packages = _result_by_key(results, "packages")
    assert packages.ok
    assert "Pakete installiert" in packages.detail
    assert set(installed) == set(launcher_checks.REQ_PKGS)


def test_missing_runtime_packages_checks_pip_and_import(monkeypatch):
    state = {
        "PySide6": (True, True),
        "Pillow": (True, False),
        "ffmpeg-python": (False, False),
    }

    monkeypatch.setattr(
        launcher_checks,
        "pip_show",
        lambda py, pkg: state[pkg][0],
    )
    monkeypatch.setattr(
        launcher_checks,
        "module_import_ok",
        lambda py, module: (
            state[
                next(
                    key
                    for key, value in launcher_checks.PACKAGE_IMPORT_NAMES.items()
                    if value == module
                )
            ][1]
        ),
    )

    missing = launcher_checks.missing_runtime_packages("python")

    assert missing == ["Pillow", "ffmpeg-python"]


if __name__ == "__main__":
    unittest.main()


def test_unresolved_todo_items_detects_open_tasks(tmp_path):
    todo = tmp_path / "todo.txt"
    todo.write_text(
        "- [x] fertig\n- [ ] offen 1\n- [ ] offen 2\n", encoding="utf-8"
    )

    unresolved = launcher_checks.unresolved_todo_items(todo)

    assert unresolved == ["offen 1", "offen 2"]


def test_evaluate_release_readiness_reports_missing_files(tmp_path):
    (tmp_path / "todo.txt").write_text("- [ ] offen\n", encoding="utf-8")

    results = launcher_checks.evaluate_release_readiness(tmp_path)

    todo_result = _result_by_key(results, "todo")
    assert not todo_result.ok
    assert "Noch offen" in todo_result.detail

    quality_result = _result_by_key(results, "quality_script")
    assert not quality_result.ok
    assert "Fehlt" in quality_result.detail


def test_evaluate_release_readiness_ok_when_basics_exist(tmp_path):
    (tmp_path / "todo.txt").write_text("- [x] fertig\n", encoding="utf-8")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "quality_check.sh").write_text(
        "#!/usr/bin/env bash\n", encoding="utf-8"
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")

    results = launcher_checks.evaluate_release_readiness(tmp_path)

    assert all(result.ok for result in results)
