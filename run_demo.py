"""Simple CLI demo for the PCF mapping prototype.

Default interactive flow:
  python run_demo.py

You can still pass arguments for automation:
  python run_demo.py --ef-excel ./emission_factor.xlsx --name "VMQ" --geo KR --unit kg --use-ai
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
from pprint import pprint
from urllib import error, request

from mapping_engine import MappingEngine, load_ef_excel

# Optional direct key input (not recommended for production).
# If you want, you can write your key here.
DEMO_GEMINI_API_KEY = ""


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


def _extract_json_object(text: str) -> dict:
    text = text.strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")

    return json.loads(text[start : end + 1])


def _call_gemini_structured(payload: dict, api_key: str, model: str, timeout: int = 20) -> dict:
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    prompt = {
        "instruction": (
            "Return only JSON with keys: "
            "name_type, canonical_form, category, state, function_hint, decomposition_suggestion, "
            "proxy_candidates, confidence, review_required, reason"
        ),
        "input": payload,
    }

    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": json.dumps(prompt, ensure_ascii=False)}],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }

    req = request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with request.urlopen(req, timeout=timeout) as resp:
        response_json = json.loads(resp.read().decode("utf-8"))

    candidates = response_json.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini returned no candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise ValueError("Gemini returned empty parts")

    text = "".join(part.get("text", "") for part in parts)
    parsed = _extract_json_object(text)

    # Keep only expected contract keys with safe defaults.
    return {
        "name_type": parsed.get("name_type", "material"),
        "canonical_form": parsed.get("canonical_form", payload.get("canonical_hint", "")),
        "category": parsed.get("category", "material"),
        "state": parsed.get("state", ""),
        "function_hint": parsed.get("function_hint", ""),
        "decomposition_suggestion": parsed.get("decomposition_suggestion", []),
        "proxy_candidates": parsed.get("proxy_candidates", []),
        "confidence": float(parsed.get("confidence", 0.0)),
        "review_required": bool(parsed.get("review_required", True)),
        "reason": parsed.get("reason", "Gemini response"),
    }


def gemini_assist_from_api_key(api_key: str, model: str):
    """Real Gemini integration with safe fallback."""

    def _ai(payload):
        if not api_key:
            return {
                "proxy_candidates": ["ecoinvent:eng_plastic_proxy_dataset"],
                "confidence": 0.62,
                "review_required": True,
                "reason": "Gemini key not set, using local AI stub",
            }

        try:
            return _call_gemini_structured(payload, api_key=api_key, model=model)
        except (error.URLError, error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            return {
                "proxy_candidates": ["ecoinvent:eng_plastic_proxy_dataset"],
                "confidence": 0.55,
                "review_required": True,
                "reason": f"Gemini call failed, fallback used: {exc}",
            }

    return _ai


def resolve_excel_path(interactive: bool, arg_path: str | None) -> str | None:
    if arg_path:
        return arg_path

    default_name = "emission_factor.xlsx"
    default_path = Path.cwd() / default_name
    if default_path.exists():
        return str(default_path)

    if not interactive:
        return None

    raw = input(f"엑셀 경로 입력 (없으면 엔터, 기본파일명 {default_name}): ").strip()
    if not raw:
        return None
    return raw


def resolve_ai_mode(interactive: bool, use_ai_arg: bool, key_arg: str | None) -> tuple[bool, str]:
    if use_ai_arg:
        key = key_arg or os.getenv("GEMINI_API_KEY", "") or DEMO_GEMINI_API_KEY
        return True, key

    if not interactive:
        return False, ""

    answer = input("Gemini AI fallback 사용? (y/N): ").strip().lower()
    if answer not in {"y", "yes"}:
        return False, ""

    key = key_arg or os.getenv("GEMINI_API_KEY", "") or DEMO_GEMINI_API_KEY
    if not key:
        key = getpass.getpass("GEMINI_API_KEY 입력(화면에 표시되지 않음): ").strip()

    return True, key


def main():
    parser = argparse.ArgumentParser(description="Run a mapping demo with sample knowledge or Excel EF table")
    parser.add_argument("--name", help="Activity name to map (if omitted, interactive prompt is used)")
    parser.add_argument("--geo", default="", help="Geography hint (e.g., KR, US, GLO, RoW)")
    parser.add_argument("--unit", default="", help="Reference product unit hint (e.g., kg, kWh)")
    parser.add_argument("--ef-excel", help="Path to Excel with columns: Activity Name, Geography, Reference Product Name, Reference Product Unit")
    parser.add_argument("--use-ai", action="store_true", help="Enable AI fallback for unresolved names")
    parser.add_argument("--gemini-model", default="gemini-2.0-flash", help="Gemini model name")
    parser.add_argument("--gemini-api-key", help="Optional Gemini key override. Prefer GEMINI_API_KEY env var.")
    args = parser.parse_args()

    interactive = args.name is None

    knowledge = build_default_knowledge()
    ef_path = resolve_excel_path(interactive, args.ef_excel)
    if ef_path:
        knowledge.update(load_ef_excel(ef_path))
        print(f"[INFO] EF 엑셀 로딩 완료: {ef_path}")
    else:
        print("[INFO] EF 엑셀 없이 기본 샘플 지식으로 실행합니다.")

    use_ai, gemini_key = resolve_ai_mode(interactive, args.use_ai, args.gemini_api_key)
    ai = gemini_assist_from_api_key(gemini_key, args.gemini_model) if use_ai else None

    engine = MappingEngine(knowledge, ai_assist=ai)

    print("=== Mapping Demo ===")
    activity_name = args.name if args.name else input("물질/활동명 입력: ").strip()
    geography = args.geo if args.geo else (input("Geography (optional): ").strip() if interactive else "")
    unit = args.unit if args.unit else (input("Unit (optional): ").strip() if interactive else "")

    result = engine.map_activity(activity_name, geography_hint=geography, unit_hint=unit)

    print("\n=== Result ===")
    pprint(result)

    if interactive:
        input("\n엔터를 누르면 종료됩니다.")


if __name__ == "__main__":
    main()
