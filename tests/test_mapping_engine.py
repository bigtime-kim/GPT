import unittest

from mapping_engine import MappingEngine, required_uploads


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

    def test_ai_assist_called_only_when_needed(self):
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
        self.assertNotIn("ai_assist_called=true", deterministic.trace_log)

        ambiguous = engine.map_activity("Thermiga 80127")
        self.assertEqual(calls["count"], 1)
        self.assertEqual(ambiguous.status, "review")
        self.assertEqual(ambiguous.selected_dataset, "ecoinvent:eng_plastic_proxy_dataset")

    def test_required_uploads(self):
        self.assertIn("api_key", required_uploads("ai_connection"))
        self.assertIn("db_catalog.xlsx", required_uploads("knowledge_bootstrap"))
        self.assertIn("approved_mapping_registry.xlsx", required_uploads("go_live"))


if __name__ == "__main__":
    unittest.main()
