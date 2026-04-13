from __future__ import annotations

import hashlib
import http.client
import json
import re
from urllib import error, request


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


def normalize_gemini_key(raw: str) -> str:
    if not raw:
        return ""
    text = raw.strip().replace("\x00", "").replace("\x01", "")
    text = "".join(ch for ch in text if ch.isprintable() and not ch.isspace())
    m = re.search(r"AIza[A-Za-z0-9_-]{20,}", text)
    if m:
        return m.group(0)
    return text


def _call_gemini_structured(payload: dict, api_key: str, model: str, timeout: int = 20) -> dict:
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": json.dumps(
                            {
                                "instruction": (
                                    "Return only JSON with keys: "
                                    "name_type, canonical_form, category, state, function_hint, decomposition_suggestion, "
                                    "proxy_candidates, confidence, review_required, reason"
                                ),
                                "input": payload,
                            },
                            ensure_ascii=False,
                        )
                    }
                ],
            }
        ],
        "generationConfig": {"temperature": 0.1},
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

    parsed = _extract_json_object("".join(part.get("text", "") for part in parts))
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


class AIResolver:
    """Boundary module for all AI calls + cache access."""

    def __init__(self, api_key: str, model: str, registry=None):
        self.api_key = api_key
        self.model = model
        self.registry = registry

    @staticmethod
    def _payload_key(payload: dict) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

    def resolve(self, payload: dict) -> dict:
        top = payload.get("search_top_n", [])
        fallback = top[0] if top else "ecoinvent:eng_plastic_proxy_dataset"
        if not self.api_key:
            return {
                "proxy_candidates": [fallback],
                "confidence": 0.0,
                "review_required": True,
                "reason": "AI unavailable (missing key), deterministic fallback only",
                "source": "ai_fallback",
            }

        key = self._payload_key(payload)
        if self.registry:
            cached = self.registry.get_ai_cache(key)
            if cached is not None:
                out = dict(cached)
                out["source"] = "ai_cache"
                return out

        try:
            out = _call_gemini_structured(payload, api_key=self.api_key, model=self.model)
            out["source"] = "gemini_live"
        except (error.URLError, error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError, http.client.InvalidURL) as exc:
            out = {
                "proxy_candidates": [fallback],
                "confidence": 0.0,
                "review_required": True,
                "reason": f"AI unavailable ({exc}), deterministic fallback only",
                "source": "ai_fallback",
            }

        if self.registry:
            self.registry.set_ai_cache(key, out)
        return out
