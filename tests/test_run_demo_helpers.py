import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from run_demo import _extract_json_object, get_default_ef_path, resolve_ai_mode


class RunDemoHelperTest(unittest.TestCase):
    def test_extract_json_object_plain(self):
        parsed = _extract_json_object('{"confidence":0.9,"proxy_candidates":["a"]}')
        self.assertEqual(parsed["confidence"], 0.9)

    def test_extract_json_object_markdown_block(self):
        parsed = _extract_json_object('```json\n{"review_required":true}\n```')
        self.assertTrue(parsed["review_required"])

    def test_get_default_ef_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path.cwd()
            os.chdir(tmp)
            try:
                path = get_default_ef_path()
                self.assertTrue(str(path).endswith("emission_factor.xlsx"))
            finally:
                os.chdir(original)

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
