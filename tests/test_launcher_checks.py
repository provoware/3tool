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


if __name__ == "__main__":
    unittest.main()
