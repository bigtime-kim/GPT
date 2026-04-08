import importlib.util
import tempfile
import unittest
from pathlib import Path

from mapping_engine import MappingEngine, load_ef_excel, required_uploads


class MappingEngineTest(unittest.TestCase):
    def setUp(self):
        self.knowledge = {
            "abbreviation": {"vmq": "silicone rubber family"},
            "synonym": {"en aw 6005a t6": "wrought aluminium extrusion family"},
            "family": {
                "silicone rubber family": "silicone rubber",
                "wrought aluminium extrusion family": "wrought aluminium extrusion family",
            },
            "proxy": {"pbt/pom": "engineering plastic"},
            "db_catalog": {
                "silicone rubber": "ecoinvent:silicone_rubber_dataset",
                "wrought aluminium extrusion family": "ecoinvent:alu_extrusion_dataset",
                "engineering plastic": "ecoinvent:eng_plastic_proxy_dataset",
            },
        }

    def test_exact_from_abbreviation(self):
        engine = MappingEngine(self.knowledge)
        result = engine.map_activity("VMQ")

        self.assertEqual(result.status, "family")
        self.assertEqual(result.selected_dataset, "ecoinvent:silicone_rubber_dataset")
        self.assertTrue(result.review_required)

    def test_spec_synonym_match(self):
        engine = MappingEngine(self.knowledge)
        result = engine.map_activity("EN AW 6005A T6")

        self.assertEqual(result.selected_dataset, "ecoinvent:alu_extrusion_dataset")

    def test_ai_assist_called_for_reranking_and_unresolved(self):
        calls = {"count": 0}

        def fake_ai(_payload):
            calls["count"] += 1
            return {
                "proxy_candidates": ["ecoinvent:eng_plastic_proxy_dataset"],
                "confidence": 0.62,
                "review_required": True,
                "reason": "Long-tail trade name interpreted",
            }

        engine = MappingEngine(self.knowledge, ai_assist=fake_ai)

        deterministic = engine.map_activity("VMQ")
        self.assertIn("ai_assist_called=true", deterministic.trace_log)

        ambiguous = engine.map_activity("Thermiga 80127")
        self.assertEqual(calls["count"], 2)
        self.assertEqual(ambiguous.status, "review")
        self.assertEqual(ambiguous.selected_dataset, "ecoinvent:eng_plastic_proxy_dataset")

    def test_required_uploads(self):
        self.assertIn("gemini_api_key", required_uploads("ai_connection"))
        self.assertIn(
            "emission_factor.xlsx(Activity Name, Geography, Reference Product Name, Reference Product Unit)",
            required_uploads("knowledge_bootstrap"),
        )
        self.assertIn("approved_mapping_registry.xlsx", required_uploads("go_live"))

    @unittest.skipUnless(importlib.util.find_spec("openpyxl") is not None, "openpyxl not installed")
    def test_load_ef_excel_and_map_by_geography(self):
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.append(["Activity Name", "Geography", "Reference Product Name", "Reference Product Unit"])
        ws.append(["electricity, medium voltage", "KR", "market for electricity, medium voltage", "kWh"])
        ws.append(["electricity, medium voltage", "RoW", "market for electricity, medium voltage", "kWh"])

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ef.xlsx"
            wb.save(path)

            ef_knowledge = load_ef_excel(str(path))
            merged = dict(self.knowledge)
            merged.update(ef_knowledge)
            engine = MappingEngine(merged)

            result = engine.map_activity("electricity, medium voltage", geography_hint="KR", unit_hint="kWh")
            self.assertEqual(result.status, "exact")
            self.assertIn("(kr)", result.selected_dataset.lower())


if __name__ == "__main__":
    unittest.main()
