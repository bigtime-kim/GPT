"""Minimal deterministic mapping engine prototype for local testing.

This module demonstrates the architecture split:
- deterministic core mapping pipeline
- optional AI assist invoked only for ambiguous/long-tail inputs
- external knowledge provided as injected dictionaries (Excel-export equivalent)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


AUTO_ACCEPT_THRESHOLD = 0.9


@dataclass
class StandardActivity:
    raw_name: str
    normalized_name: str
    canonical_form: str
    name_type: str
    category: str
    role: str = "input"
    state: str = ""
    function_hint: str = ""
    hierarchy_level: str = ""
    treatment_route: str = ""
    geography_hint: str = ""
    source_type: str = ""
    mapping_mode: str = "material"
    trace_log: List[str] = field(default_factory=list)


@dataclass
class MappingResult:
    status: str  # exact, family, proxy, composite, review
    selected_dataset: Optional[str]
    confidence: float
    review_required: bool
    reason: str
    trace_log: List[str]


class MappingEngine:
    def __init__(self, knowledge: Dict[str, Dict[str, str]], ai_assist: Optional[Callable[[Dict], Dict]] = None):
        self.knowledge = knowledge
        self.ai_assist = ai_assist

    def preprocess(self, name: str) -> str:
        normalized = " ".join(name.strip().lower().replace("/", " /").split())
        return normalized

    def classify_name_type(self, normalized_name: str) -> str:
        if any(k in normalized_name for k in ["waste", "폐", "sludge", "leachate"]):
            return "waste"
        if any(k in normalized_name for k in ["electricity", "lng", "steam", "heat"]):
            return "energy"
        if "wastewater" in normalized_name or "폐수" in normalized_name:
            return "wastewater"
        if any(token in normalized_name for token in ["en aw", "aisi", "alsi"]):
            return "spec"
        if normalized_name.replace(" ", "") in self.knowledge.get("abbreviation", {}):
            return "abbreviation"
        return "material"

    def canonicalize(self, normalized_name: str, name_type: str) -> str:
        if name_type == "abbreviation":
            key = normalized_name.replace(" ", "")
            return self.knowledge["abbreviation"][key]

        synonyms = self.knowledge.get("synonym", {})
        return synonyms.get(normalized_name, normalized_name)

    def generate_candidates(self, canonical_form: str) -> List[str]:
        catalog = self.knowledge.get("db_catalog", {})
        if canonical_form in catalog:
            return [catalog[canonical_form]]

        families = self.knowledge.get("family", {})
        if canonical_form in families and families[canonical_form] in catalog:
            return [catalog[families[canonical_form]]]

        proxies = self.knowledge.get("proxy", {})
        if canonical_form in proxies and proxies[canonical_form] in catalog:
            return [catalog[proxies[canonical_form]]]

        return []

    def map_activity(self, raw_name: str, source_type: str = "") -> MappingResult:
        normalized = self.preprocess(raw_name)
        name_type = self.classify_name_type(normalized)
        canonical = self.canonicalize(normalized, name_type)

        trace = [
            f"preprocess={normalized}",
            f"name_type={name_type}",
            f"canonical={canonical}",
        ]

        candidates = self.generate_candidates(canonical)

        if candidates:
            status = "exact"
            if canonical in self.knowledge.get("family", {}):
                status = "family"
            if canonical in self.knowledge.get("proxy", {}):
                status = "proxy"

            confidence = {"exact": 0.98, "family": 0.85, "proxy": 0.7}[status]
            review_required = confidence < AUTO_ACCEPT_THRESHOLD
            reason = f"Deterministic {status} candidate generated"
            return MappingResult(status, candidates[0], confidence, review_required, reason, trace)

        # AI assist is intentionally only for unresolved / long-tail cases.
        if self.ai_assist:
            ai_request = {
                "raw_name": raw_name,
                "source_type": source_type,
                "normalized_name": normalized,
                "canonical_hint": canonical,
                "knowledge_hits": [],
            }
            ai_response = self.ai_assist(ai_request)
            trace.append("ai_assist_called=true")

            proxy_candidates = ai_response.get("proxy_candidates", [])
            confidence = float(ai_response.get("confidence", 0.0))
            selected = proxy_candidates[0] if proxy_candidates else None
            review_required = ai_response.get("review_required", True)
            status = "review" if review_required else "proxy"
            reason = ai_response.get("reason", "AI assist fallback")
            return MappingResult(status, selected, confidence, review_required, reason, trace)

        trace.append("ai_assist_called=false")
        return MappingResult(
            status="review",
            selected_dataset=None,
            confidence=0.0,
            review_required=True,
            reason="No deterministic candidate found",
            trace_log=trace,
        )


def required_uploads(stage: str) -> List[str]:
    """Return user-upload requirements per delivery stage."""
    stage = stage.lower()
    if stage == "ai_connection":
        return ["api_key", "model", "rate_limit_policy"]
    if stage == "knowledge_bootstrap":
        return [
            "db_catalog.xlsx",
            "synonym_abbreviation.xlsx",
            "material_ontology.xlsx",
            "spec_alloy_master.xlsx",
            "waste_matrix.xlsx",
            "energy_wastewater.xlsx",
            "policy_table.xlsx",
            "mapping_registry.xlsx",
        ]
    if stage == "go_live":
        return ["policy_geography_table.xlsx", "approved_mapping_registry.xlsx"]
    raise ValueError(f"Unknown stage: {stage}")
