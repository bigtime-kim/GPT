"""Simple CLI demo for the PCF mapping prototype.

Interactive mode (default):
  python run_demo.py

Non-interactive mode:
  python run_demo.py --name "VMQ"

AI mode with API key from env:
  export OPENAI_API_KEY="..."
  python run_demo.py --use-ai
"""

from __future__ import annotations

import argparse
import os
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


def ai_assist_from_api_key(api_key: str):
    """Placeholder for real AI integration.

    Where to put API key:
      - Recommended: environment variable OPENAI_API_KEY
      - Optional: pass --api-key directly (not recommended for production)
    """

    def _ai(payload):
        # TODO: Replace with real API call.
        # Example integration point:
        # 1) Build structured request from payload
        # 2) Send to LLM API using api_key
        # 3) Parse JSON response into required schema
        if not api_key:
            return fake_ai(payload)

        return {
            "proxy_candidates": ["ecoinvent:eng_plastic_proxy_dataset"],
            "confidence": 0.65,
            "review_required": True,
            "reason": "AI fallback stub used (replace with real API call)",
        }

    return _ai


def main():
    parser = argparse.ArgumentParser(description="Run a mapping demo with sample knowledge")
    parser.add_argument("--name", help="Activity name to map (if omitted, interactive prompt is used)")
    parser.add_argument("--use-ai", action="store_true", help="Enable AI fallback for unresolved names")
    parser.add_argument("--api-key", help="Optional API key override. Prefer OPENAI_API_KEY env var.")
    args = parser.parse_args()

    api_key = args.api_key or os.getenv("OPENAI_API_KEY", "")
    ai = ai_assist_from_api_key(api_key) if args.use_ai else None

    engine = MappingEngine(build_knowledge(), ai_assist=ai)

    print("=== Mapping Demo ===")
    activity_name = args.name if args.name else input("활동명 입력: ").strip()

    result = engine.map_activity(activity_name)

    print("\n=== Result ===")
    pprint(result)

    if not args.name:
        input("\n엔터를 누르면 종료됩니다.")


if __name__ == "__main__":
    main()
