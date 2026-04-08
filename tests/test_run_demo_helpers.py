import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from run_demo import (
    _extract_json_object,
    get_ef_search_paths,
    load_fixed_ef_knowledge,
    locate_ef_file,
    normalize_gemini_key,
    resolve_ai_mode,
)


class RunDemoHelperTest(unittest.TestCase):
    def test_extract_json_object_plain(self):
        parsed = _extract_json_object('{"confidence":0.9,"proxy_candidates":["a"]}')
        self.assertEqual(parsed["confidence"], 0.9)

    def test_extract_json_object_markdown_block(self):
        parsed = _extract_json_object('```json\n{"review_required":true}\n```')
        self.assertTrue(parsed["review_required"])

    def test_get_ef_search_paths(self):
        paths = get_ef_search_paths()
        self.assertGreaterEqual(len(paths), 6)
        names = {p.name for p in paths}
        self.assertIn("emission_factor.xlsx", names)
        self.assertIn("emission_factor.csv", names)

    def test_locate_ef_file_finds_in_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path.cwd()
            os.chdir(tmp)
            try:
                ef = Path(tmp) / "emission_factor.xlsx"
                ef.write_text("dummy")
                found = locate_ef_file()
                self.assertIsNotNone(found)
                self.assertEqual(found.resolve(), ef.resolve())
            finally:
                os.chdir(original)

    def test_load_fixed_ef_knowledge_raises_on_error(self):
        with patch("run_demo.locate_ef_file", return_value=Path("dummy.xlsx")), patch(
            "run_demo.load_ef_file", side_effect=RuntimeError("boom")
        ):
            with self.assertRaises(RuntimeError):
                load_fixed_ef_knowledge({"db_catalog": {}})

    def test_resolve_ai_mode_requires_key(self):
        with patch("builtins.input", return_value=""):
            with self.assertRaises(ValueError):
                resolve_ai_mode(interactive=True, disable_ai_arg=False, key_arg=None)

    def test_resolve_ai_mode_accepts_prompt_key(self):
        with patch("builtins.input", return_value="abc123"):
            use_ai, key = resolve_ai_mode(interactive=True, disable_ai_arg=False, key_arg=None)
            self.assertTrue(use_ai)
            self.assertEqual(key, "abc123")

    def test_resolve_ai_mode_can_disable(self):
        use_ai, key = resolve_ai_mode(interactive=True, disable_ai_arg=True, key_arg=None)
        self.assertFalse(use_ai)
        self.assertEqual(key, "")

    def test_normalize_gemini_key(self):
        raw = "  AIzaSyTESTKEY1234567890abcdEFGHijklmn\x01\x01  EXTRA_TEXT"
        normalized = normalize_gemini_key(raw)
        self.assertTrue(normalized.startswith("AIza"))
        self.assertNotIn("\x01", normalized)


if __name__ == "__main__":
    unittest.main()
