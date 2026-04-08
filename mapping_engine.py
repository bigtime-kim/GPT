"""Minimal deterministic mapping engine prototype for local testing.

This module demonstrates the architecture split:
- deterministic core mapping pipeline
- optional AI assist invoked only for ambiguous/long-tail inputs
- external knowledge provided as injected dictionaries (Excel-export equivalent)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Callable, Dict, List, Optional


AUTO_ACCEPT_THRESHOLD = 0.9
REQUIRED_EF_COLUMNS = [
    "Activity Name",
    "Geography",
    "Reference Product Name",
    "Reference Product Unit",
]


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

    @staticmethod
    def _sim(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    def _fuzzy_ef_candidate(self, canonical_form: str, geography_hint: str, unit_hint: str) -> Optional[str]:
        records = self.knowledge.get("ef_records", [])
        if not records:
            return None

        geo = (geography_hint or "").strip().lower()
        unit = (unit_hint or "").strip().lower()

        candidates = []
        for rec in records:
            # Soft filter by geography/unit if provided.
            geo_ok = not geo or rec["geography"] in {geo, "", "row", "glo"}
            unit_ok = not unit or rec["unit"] in {unit, ""}
            if not geo_ok or not unit_ok:
                continue

            score = self._sim(canonical_form, rec["activity"])
            if score >= 0.55:
                candidates.append((score, rec["dataset"]))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def generate_candidates(
        self,
        canonical_form: str,
        geography_hint: str = "",
        unit_hint: str = "",
    ) -> List[str]:
        catalog = self.knowledge.get("db_catalog", {})

        if canonical_form in catalog:
            return [catalog[canonical_form]]

        families = self.knowledge.get("family", {})
        if canonical_form in families and families[canonical_form] in catalog:
            return [catalog[families[canonical_form]]]

        proxies = self.knowledge.get("proxy", {})
        if canonical_form in proxies and proxies[canonical_form] in catalog:
            return [catalog[proxies[canonical_form]]]

        # Emission factor table candidate matching with geography fallback.
        ef_rows = self.knowledge.get("ef_rows", {})
        if ef_rows:
            geo = (geography_hint or "").strip().lower()
            unit = (unit_hint or "").strip().lower()
            keys = []
            if geo:
                keys.append(f"{canonical_form}|{geo}|{unit}")
                keys.append(f"{canonical_form}|{geo}|")
            keys.append(f"{canonical_form}|row|{unit}")
            keys.append(f"{canonical_form}|row|")
            keys.append(f"{canonical_form}|glo|{unit}")
            keys.append(f"{canonical_form}|glo|")
            keys.append(f"{canonical_form}||{unit}")
            keys.append(f"{canonical_form}||")

            for key in keys:
                if key in ef_rows:
                    return [ef_rows[key]]

        fuzzy = self._fuzzy_ef_candidate(canonical_form, geography_hint, unit_hint)
        if fuzzy:
            return [fuzzy]

        return []

    def map_activity(
        self,
        raw_name: str,
        source_type: str = "",
        geography_hint: str = "",
        unit_hint: str = "",
    ) -> MappingResult:
        normalized = self.preprocess(raw_name)
        name_type = self.classify_name_type(normalized)
        canonical = self.canonicalize(normalized, name_type)

        trace = [
            f"preprocess={normalized}",
            f"name_type={name_type}",
            f"canonical={canonical}",
            f"geography_hint={geography_hint}",
            f"unit_hint={unit_hint}",
        ]

        candidates = self.generate_candidates(canonical, geography_hint, unit_hint)

        if candidates:
            status = "exact"
            if canonical in self.knowledge.get("family", {}):
                status = "family"
            if canonical in self.knowledge.get("proxy", {}):
                status = "proxy"

            if self.knowledge.get("ef_rows", {}) or self.knowledge.get("ef_records", {}):
                status = "exact"

            confidence = {"exact": 0.98, "family": 0.85, "proxy": 0.7}[status]
            review_required = confidence < AUTO_ACCEPT_THRESHOLD
            reason = f"Deterministic {status} candidate generated"
            selected = candidates[0]

            # AI re-interpretation/reranking stage (if available), even after deterministic hit.
            if self.ai_assist:
                ai_request = {
                    "raw_name": raw_name,
                    "source_type": source_type,
                    "normalized_name": normalized,
                    "canonical_hint": canonical,
                    "geography_hint": geography_hint,
                    "unit_hint": unit_hint,
                    "search_top_n": candidates[:3],
                }
                ai_response = self.ai_assist(ai_request)
                trace.append("ai_assist_called=true")
                ai_candidates = ai_response.get("proxy_candidates", [])
                if ai_candidates:
                    selected = ai_candidates[0]
                    confidence = float(ai_response.get("confidence", confidence))
                    review_required = ai_response.get("review_required", review_required)
                    reason = ai_response.get("reason", reason)

            return MappingResult(status, selected, confidence, review_required, reason, trace)

        # AI assist is intentionally only for unresolved / long-tail cases.
        if self.ai_assist:
            ai_request = {
                "raw_name": raw_name,
                "source_type": source_type,
                "normalized_name": normalized,
                "canonical_hint": canonical,
                "geography_hint": geography_hint,
                "unit_hint": unit_hint,
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


def load_ef_excel(path: str) -> Dict[str, Dict[str, str]]:
    """Load emission factor rows from Excel with required columns."""

    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ImportError("openpyxl is required to read .xlsx files. Install with `pip install openpyxl`.") from exc

    xlsx_path = Path(path)
    wb = load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active

    rows = ws.iter_rows(min_row=1, max_row=1, values_only=True)
    header = [str(col).strip() if col is not None else "" for col in next(rows)]

    missing = [c for c in REQUIRED_EF_COLUMNS if c not in header]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    index = {name: header.index(name) for name in REQUIRED_EF_COLUMNS}

    ef_rows: Dict[str, str] = {}
    ef_records: List[Dict[str, str]] = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        activity = str(row[index["Activity Name"]] or "").strip().lower()
        geography = str(row[index["Geography"]] or "").strip().lower()
        ref_name = str(row[index["Reference Product Name"]] or "").strip()
        ref_unit = str(row[index["Reference Product Unit"]] or "").strip().lower()

        if not activity:
            continue

        dataset_value = f"{ref_name} [{ref_unit}] ({geography or 'unspecified geo'})"
        key = f"{activity}|{geography}|{ref_unit}"
        ef_rows[key] = dataset_value

        key_no_unit = f"{activity}|{geography}|"
        ef_rows.setdefault(key_no_unit, dataset_value)

        ef_records.append(
            {
                "activity": activity,
                "geography": geography,
                "unit": ref_unit,
                "dataset": dataset_value,
            }
        )

    return {"ef_rows": ef_rows, "ef_records": ef_records}


def required_uploads(stage: str) -> List[str]:
    """Return user-upload requirements per delivery stage."""
    stage = stage.lower()
    if stage == "ai_connection":
        return ["gemini_api_key", "gemini_model", "rate_limit_policy"]
    if stage == "knowledge_bootstrap":
        return [
            "emission_factor.xlsx(Activity Name, Geography, Reference Product Name, Reference Product Unit)",
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
