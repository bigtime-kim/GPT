"""Simple CLI demo for the PCF mapping prototype.

Interactive mode (default):
  python run_demo.py

Use Excel emission-factor table:
  python run_demo.py --ef-excel ./emission_factor.xlsx

AI mode with Gemini key from env:
  export GEMINI_API_KEY="..."
  python run_demo.py --use-ai
"""

from __future__ import annotations

import argparse
import os
from pprint import pprint

from mapping_engine import MappingEngine, load_ef_excel


def build_default_knowledge():
    return {
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


def gemini_assist_from_api_key(api_key: str, model: str):
    """Placeholder for Gemini integration.

    Recommended key location:
    - GEMINI_API_KEY environment variable
    """

    def _ai(_payload):
        if not api_key:
            return {
                "proxy_candidates": ["ecoinvent:eng_plastic_proxy_dataset"],
                "confidence": 0.62,
                "review_required": True,
                "reason": "Gemini key not set, using local AI stub",
            }

        # TODO: Replace with real Gemini API request.
        return {
            "proxy_candidates": ["ecoinvent:eng_plastic_proxy_dataset"],
            "confidence": 0.67,
            "review_required": True,
            "reason": f"Gemini stub used (model={model}); wire real API call here",
        }

    return _ai


def main():
    parser = argparse.ArgumentParser(description="Run a mapping demo with sample knowledge or Excel EF table")
    parser.add_argument("--name", help="Activity name to map (if omitted, interactive prompt is used)")
    parser.add_argument("--geo", default="", help="Geography hint (e.g., KR, US, GLO, RoW)")
    parser.add_argument("--unit", default="", help="Reference product unit hint (e.g., kg, kWh)")
    parser.add_argument("--ef-excel", help="Path to Excel with columns: Activity Name, Geography, Reference Product Name, Reference Product Unit")
    parser.add_argument("--use-ai", action="store_true", help="Enable AI fallback for unresolved names")
    parser.add_argument("--gemini-model", default="gemini-2.5-pro", help="Gemini model name")
    parser.add_argument("--gemini-api-key", help="Optional Gemini key override. Prefer GEMINI_API_KEY env var.")
    args = parser.parse_args()

    knowledge = build_default_knowledge()
    if args.ef_excel:
        knowledge.update(load_ef_excel(args.ef_excel))

    gemini_key = args.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
    ai = gemini_assist_from_api_key(gemini_key, args.gemini_model) if args.use_ai else None

    engine = MappingEngine(knowledge, ai_assist=ai)

    print("=== Mapping Demo ===")
    activity_name = args.name if args.name else input("활동명 입력: ").strip()
    geography = args.geo if args.geo else (input("Geography (optional): ").strip() if not args.name else "")
    unit = args.unit if args.unit else (input("Unit (optional): ").strip() if not args.name else "")

    result = engine.map_activity(activity_name, geography_hint=geography, unit_hint=unit)

    print("\n=== Result ===")
    pprint(result)

    if not args.name:
        input("\n엔터를 누르면 종료됩니다.")


if __name__ == "__main__":
    main()
