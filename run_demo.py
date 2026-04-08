"""Simple CLI demo for the PCF mapping prototype.

Default interactive flow:
  python run_demo.py

You can still pass arguments for automation:
  python run_demo.py --name "VMQ" --geo KR --unit kg --use-ai
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from pathlib import Path
from pprint import pprint
from urllib import error, request

from mapping_engine import MappingEngine, load_ef_excel

# Optional direct key input (not recommended for production).
# If you want, you can write your key here.
DEMO_GEMINI_API_KEY = ""
DEFAULT_EF_FILENAME = "emission_factor.xlsx"


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
            "temperature": 0.1
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
            top = payload.get("search_top_n", [])
            fallback = top[0] if top else "ecoinvent:eng_plastic_proxy_dataset"
            return {
                "proxy_candidates": [fallback],
                "confidence": 0.80,
                "review_required": False if top else True,
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


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_ef_search_paths() -> list[Path]:
    return [
        Path.cwd() / DEFAULT_EF_FILENAME,
        _get_base_dir() / DEFAULT_EF_FILENAME,
        _get_base_dir().parent / DEFAULT_EF_FILENAME,
    ]


def locate_ef_file() -> Path | None:
    for path in get_ef_search_paths():
        if path.exists():
            return path
    return None


def _list_excel_hints() -> list[str]:
    """Collect nearby excel files for troubleshooting when fixed filename isn't found."""
    hints: list[str] = []
    seen = set()
    for candidate in get_ef_search_paths():
        folder = candidate.parent
        if folder in seen or not folder.exists():
            continue
        seen.add(folder)
        for p in folder.glob("*.xls*"):
            hints.append(str(p.resolve()))
    return hints[:10]


def load_fixed_ef_knowledge(knowledge: dict) -> dict:
    """Load fixed-name EF file in strict mode. Raises on any issue."""
    ef_path = locate_ef_file()
    if not ef_path:
        lines = [f"{DEFAULT_EF_FILENAME} 파일을 찾지 못했습니다.", "검색 경로:"]
        lines.extend([f"  - {p}" for p in get_ef_search_paths()])
        hints = _list_excel_hints()
        if hints:
            lines.append("주변 Excel 파일:")
            lines.extend([f"  - {h}" for h in hints])
        raise FileNotFoundError("\n".join(lines))

    try:
        knowledge.update(load_ef_excel(str(ef_path)))
        print(f"[INFO] EF 엑셀 로딩 완료(파일명={DEFAULT_EF_FILENAME}): {ef_path}")
        return knowledge
    except Exception as exc:
        raise RuntimeError(
            f"EF 엑셀 로딩 실패: {exc}\n"
            f"현재 python: {sys.executable}\n"
            f"이 Python에 설치: '{sys.executable}' -m pip install openpyxl\n"
            "exe 사용 중이면: pyinstaller --onefile run_demo.py --collect-all openpyxl"
        ) from exc



def print_runtime_diagnostics() -> None:
    print("[DIAG] python executable:", sys.executable)
    print("[DIAG] base dir:", _get_base_dir())
    try:
        import openpyxl  # type: ignore

        print("[DIAG] openpyxl version:", openpyxl.__version__)
    except Exception as exc:
        print("[DIAG] openpyxl import failed:", exc)


def resolve_ai_mode(interactive: bool, disable_ai_arg: bool, key_arg: str | None) -> tuple[bool, str]:
    # AI-first mode by default. Use --no-ai only for debugging.
    if disable_ai_arg:
        return False, ""

    key = key_arg or os.getenv("GEMINI_API_KEY", "") or DEMO_GEMINI_API_KEY
    if not key:
        raise ValueError("GEMINI_API_KEY is required. Set env var or pass --gemini-api-key. (Use --no-ai only for debug)")
    return True, key


def run() -> int:
    parser = argparse.ArgumentParser(description="Run a mapping demo with sample knowledge + fixed Excel file name")
    parser.add_argument("--name", help="Activity name to map (if omitted, interactive prompt is used)")
    parser.add_argument("--geo", default="", help="Geography hint (e.g., KR, US, GLO, RoW)")
    parser.add_argument("--unit", default="", help="Reference product unit hint (e.g., kg, kWh)")
    parser.add_argument("--no-ai", action="store_true", help="Disable AI (debug only). Default is AI-first mode")
    parser.add_argument("--gemini-model", default="gemini-2.0-flash", help="Gemini model name")
    parser.add_argument("--gemini-api-key", help="Optional Gemini key override. Prefer GEMINI_API_KEY env var.")
    parser.add_argument("--diag", action="store_true", help="Print runtime diagnostics (python path, openpyxl import)")
    args = parser.parse_args()

    interactive = args.name is None

    if args.diag:
        print_runtime_diagnostics()

    knowledge = build_default_knowledge()
    knowledge = load_fixed_ef_knowledge(knowledge)

    use_ai, gemini_key = resolve_ai_mode(interactive, args.no_ai, args.gemini_api_key)
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

    return 0


def main() -> int:
    try:
        return run()
    except KeyboardInterrupt:
        print("\n[INFO] 사용자 중단")
        return 130
    except Exception:
        print("\n[ERROR] 실행 중 예외가 발생했습니다:")
        traceback.print_exc()
        if sys.stdin and sys.stdin.isatty():
            input("\n엔터를 누르면 종료됩니다.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
