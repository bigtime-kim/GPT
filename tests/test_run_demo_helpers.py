import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from run_demo import resolve_ai_mode, resolve_excel_path


class RunDemoHelperTest(unittest.TestCase):
    def test_resolve_excel_path_uses_default_when_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "emission_factor.xlsx").write_text("dummy")
            original = Path.cwd()
            os.chdir(cwd)
            try:
                resolved = resolve_excel_path(interactive=True, arg_path=None)
                self.assertTrue(resolved.endswith("emission_factor.xlsx"))
            finally:
                os.chdir(original)

    def test_resolve_excel_path_from_input(self):
        with patch("builtins.input", return_value="./my.xlsx"):
            resolved = resolve_excel_path(interactive=True, arg_path=None)
            self.assertEqual(resolved, "./my.xlsx")

    def test_resolve_ai_mode_prompt_and_key_input(self):
        with patch("builtins.input", return_value="y"), patch("getpass.getpass", return_value="abc123"):
            use_ai, key = resolve_ai_mode(interactive=True, use_ai_arg=False, key_arg=None)
            self.assertTrue(use_ai)
            self.assertEqual(key, "abc123")

    def test_resolve_ai_mode_use_arg(self):
        use_ai, key = resolve_ai_mode(interactive=False, use_ai_arg=True, key_arg="my-key")
        self.assertTrue(use_ai)
        self.assertEqual(key, "my-key")


if __name__ == "__main__":
    unittest.main()
