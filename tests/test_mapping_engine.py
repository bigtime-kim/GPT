import importlib.util
import tempfile
import unittest
from pathlib import Path

from mapping_engine import MappingEngine, load_ef_excel, required_uploads
from pipeline import MappingPipeline
from registry import MappingRegistry


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

    def test_unresolved_is_review_without_ai_in_engine(self):
        engine = MappingEngine(self.knowledge)
        ambiguous = engine.map_activity("Thermiga 80127")
        self.assertEqual(ambiguous.status, "review")
        self.assertIsNone(ambiguous.selected_dataset)
        self.assertIn("candidate_source=none", ambiguous.trace_log)

    def test_required_uploads(self):
        self.assertIn("gemini_api_key", required_uploads("ai_connection"))
        self.assertIn(
            "emission_factor.xlsx|csv(Activity Name, Geography, Reference Product Name, Reference Product Unit)",
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
            wb.close()

            ef_knowledge = load_ef_excel(str(path))
            merged = dict(self.knowledge)
            merged.update(ef_knowledge)
            engine = MappingEngine(merged)

            result = engine.map_activity("electricity, medium voltage", geography_hint="KR", unit_hint="kWh")
            self.assertEqual(result.status, "exact")
            self.assertIn("(kr)", result.selected_dataset.lower())
            self.assertIn("candidate_source=ef_exact", result.trace_log)

    def test_pipeline_gate_skips_ai_for_high_conf_deterministic(self):
        calls = {"count": 0}

        class DummyAI:
            def resolve(self, _payload):
                calls["count"] += 1
                return {
                    "proxy_candidates": ["ecoinvent:eng_plastic_proxy_dataset"],
                    "confidence": 0.6,
                    "review_required": True,
                    "reason": "should not be called",
                }

        pipeline = MappingPipeline(
            engine=MappingEngine(self.knowledge),
            ai_resolver=DummyAI(),
            registry=MappingRegistry(),
            ai_threshold=0.8,
        )
        result = pipeline.map_activity("EN AW 6005A T6")
        self.assertEqual(calls["count"], 0)
        self.assertEqual(result.selected_dataset, "ecoinvent:alu_extrusion_dataset")

    def test_pipeline_uses_memo_not_approved_for_auto_reuse(self):
        registry = MappingRegistry()
        pipeline = MappingPipeline(engine=MappingEngine(self.knowledge), ai_resolver=None, registry=registry, ai_threshold=0.8)
        result = pipeline.map_activity("EN AW 6005A T6")
        self.assertEqual(result.selected_dataset, "ecoinvent:alu_extrusion_dataset")
        with self.assertRaises(NotImplementedError):
            registry.get_approved_mapping("EN AW 6005A T6")
        memo = registry.get_memo_record("wrought aluminium extrusion family")
        self.assertIsNotNone(memo)
        self.assertEqual(memo.dataset, "ecoinvent:alu_extrusion_dataset")
        self.assertEqual(memo.status, "exact")

    def test_pipeline_ai_trace_contains_source(self):
        class DummyAI:
            def resolve(self, _payload):
                return {
                    "proxy_candidates": ["ecoinvent:eng_plastic_proxy_dataset"],
                    "confidence": 0.6,
                    "review_required": True,
                    "reason": "fallback",
                    "source": "ai_cache",
                }

        pipeline = MappingPipeline(
            engine=MappingEngine(self.knowledge),
            ai_resolver=DummyAI(),
            registry=MappingRegistry(),
            ai_threshold=0.9,
        )
        result = pipeline.map_activity("VMQ")
        self.assertIn("ai_source=ai_cache", result.trace_log)

    def test_pipeline_uses_approved_record_metadata(self):
        registry = MappingRegistry()
        registry.set_approved_record(
            canonical_form="polypropylene",
            geography_hint="",
            unit_hint="",
            dataset="approved:pp",
            status="proxy",
            confidence=0.88,
            approval_type="human",
            approved_by="qa",
            reason="reviewed",
        )
        knowledge = dict(self.knowledge)
        knowledge["synonym"] = dict(self.knowledge["synonym"])
        knowledge["synonym"]["pp"] = "polypropylene"
        pipeline = MappingPipeline(engine=MappingEngine(knowledge), ai_resolver=None, registry=registry)
        result = pipeline.map_activity("PP")
        self.assertEqual(result.selected_dataset, "approved:pp")
        self.assertEqual(result.status, "proxy")
        self.assertAlmostEqual(result.confidence, 0.88)
        self.assertIn("approval_type=human", result.trace_log)

    def test_should_not_call_ai_for_catalog_exact(self):
        calls = {"count": 0}

        class DummyAI:
            def resolve(self, _payload):
                calls["count"] += 1
                return {"proxy_candidates": ["x"], "confidence": 1.0, "review_required": False, "source": "gemini_live"}

        knowledge = dict(self.knowledge)
        knowledge["db_catalog"] = dict(self.knowledge["db_catalog"])
        knowledge["db_catalog"]["polypropylene"] = "catalog:pp"
        knowledge["synonym"] = dict(self.knowledge["synonym"])
        knowledge["synonym"]["pp"] = "polypropylene"
        pipeline = MappingPipeline(engine=MappingEngine(knowledge), ai_resolver=DummyAI(), registry=MappingRegistry(), ai_threshold=0.99)
        result = pipeline.map_activity("PP")
        self.assertEqual(calls["count"], 0)
        self.assertEqual(result.selected_dataset, "catalog:pp")


if __name__ == "__main__":
    unittest.main()
