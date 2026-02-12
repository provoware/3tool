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


if __name__ == "__main__":
    unittest.main()
