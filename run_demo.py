"""Simple CLI demo for the PCF mapping prototype.

Usage:
  python run_demo.py --name "VMQ"
  python run_demo.py --name "Thermiga 80127" --use-ai
"""

from __future__ import annotations

import argparse
from pprint import pprint

from mapping_engine import MappingEngine


def build_knowledge():
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


def fake_ai(_payload):
    return {
        "proxy_candidates": ["ecoinvent:eng_plastic_proxy_dataset"],
        "confidence": 0.62,
        "review_required": True,
        "reason": "Long-tail trade name interpreted",
    }


def main():
    parser = argparse.ArgumentParser(description="Run a mapping demo with sample knowledge")
    parser.add_argument("--name", required=True, help="Activity name to map")
    parser.add_argument("--use-ai", action="store_true", help="Enable AI fallback for unresolved names")
    args = parser.parse_args()

    ai = fake_ai if args.use_ai else None
    engine = MappingEngine(build_knowledge(), ai_assist=ai)
    result = engine.map_activity(args.name)

    pprint(result)


if __name__ == "__main__":
    main()
