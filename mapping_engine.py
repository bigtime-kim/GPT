"""Minimal deterministic mapping engine prototype for local testing.

This module demonstrates the architecture split:
- deterministic core mapping pipeline
- optional AI assist invoked only for ambiguous/long-tail inputs
- external knowledge provided as injected dictionaries (Excel-export equivalent)
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
import subprocess
import sys
from typing import Dict, List, Optional


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
    def __init__(self, knowledge: Dict[str, Dict[str, str]]):
        self.knowledge = knowledge

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

    def _resolve_deterministic_candidate(
        self,
        canonical_form: str,
        geography_hint: str = "",
        unit_hint: str = "",
    ) -> tuple[Optional[str], str, float, str]:
        catalog = self.knowledge.get("db_catalog", {})
        if canonical_form in catalog:
            return catalog[canonical_form], "exact", 0.98, "catalog_exact"

        families = self.knowledge.get("family", {})
        if canonical_form in families and families[canonical_form] in catalog:
            return catalog[families[canonical_form]], "family", 0.85, "family_map"

        proxies = self.knowledge.get("proxy", {})
        if canonical_form in proxies and proxies[canonical_form] in catalog:
            return catalog[proxies[canonical_form]], "proxy", 0.7, "proxy_map"

        ef_rows = self.knowledge.get("ef_rows", {})
        if ef_rows:
            geo = (geography_hint or "").strip().lower()
            unit = (unit_hint or "").strip().lower()
            keys = []
            if geo:
                keys.append((f"{canonical_form}|{geo}|{unit}", "ef_exact"))
                keys.append((f"{canonical_form}|{geo}|", "ef_geo_fallback"))
            keys.append((f"{canonical_form}|row|{unit}", "ef_geo_fallback"))
            keys.append((f"{canonical_form}|row|", "ef_geo_fallback"))
            keys.append((f"{canonical_form}|glo|{unit}", "ef_geo_fallback"))
            keys.append((f"{canonical_form}|glo|", "ef_geo_fallback"))
            keys.append((f"{canonical_form}||{unit}", "ef_geo_fallback"))
            keys.append((f"{canonical_form}||", "ef_geo_fallback"))
            for key, source in keys:
                if key in ef_rows:
                    return ef_rows[key], "exact", 0.95, source

        fuzzy = self._fuzzy_ef_candidate(canonical_form, geography_hint, unit_hint)
        if fuzzy:
            return fuzzy, "review", 0.65, "ef_fuzzy"

        return None, "review", 0.0, "none"

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

        selected, status, confidence, source = self._resolve_deterministic_candidate(canonical, geography_hint, unit_hint)
        trace.append(f"candidate_source={source}")
        trace.append("ai_assist_called=false")
        if selected is not None:
            review_required = confidence < AUTO_ACCEPT_THRESHOLD
            return MappingResult(
                status=status,
                selected_dataset=selected,
                confidence=confidence,
                review_required=review_required,
                reason=f"Deterministic {source} candidate generated",
                trace_log=trace,
            )

        return MappingResult(
            status="review",
            selected_dataset=None,
            confidence=0.0,
            review_required=True,
            reason="No deterministic candidate found",
            trace_log=trace,
        )


def _build_ef_knowledge_from_rows(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    ef_rows: Dict[str, str] = {}
    ef_records: List[Dict[str, str]] = []

    for rec in rows:
        activity = str(rec.get("Activity Name", "") or "").strip().lower()
        geography = str(rec.get("Geography", "") or "").strip().lower()
        ref_name = str(rec.get("Reference Product Name", "") or "").strip()
        ref_unit = str(rec.get("Reference Product Unit", "") or "").strip().lower()

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


def load_ef_excel(path: str) -> Dict[str, Dict[str, str]]:
    """Load emission factor rows from .xlsx with required columns."""

    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        # Auto-heal path for non-developer users: attempt one-time install.
        install_cmd = [sys.executable, "-m", "pip", "install", "openpyxl"]
        subprocess.run(install_cmd, check=False)
        try:
            from openpyxl import load_workbook
        except ImportError as retry_exc:
            raise ImportError(
                "openpyxl is required to read .xlsx files. "
                f"Install with `{sys.executable} -m pip install openpyxl`."
            ) from retry_exc

    xlsx_path = Path(path)
    wb = load_workbook(xlsx_path, read_only=True, data_only=True)
    try:
        ws = wb.active

        rows = ws.iter_rows(min_row=1, max_row=1, values_only=True)
        header = [str(col).strip() if col is not None else "" for col in next(rows)]

        missing = [c for c in REQUIRED_EF_COLUMNS if c not in header]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        index = {name: header.index(name) for name in REQUIRED_EF_COLUMNS}

        table_rows: List[Dict[str, str]] = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            table_rows.append(
                {
                    "Activity Name": str(row[index["Activity Name"]] or ""),
                    "Geography": str(row[index["Geography"]] or ""),
                    "Reference Product Name": str(row[index["Reference Product Name"]] or ""),
                    "Reference Product Unit": str(row[index["Reference Product Unit"]] or ""),
                }
            )

        return _build_ef_knowledge_from_rows(table_rows)
    finally:
        wb.close()


def load_ef_csv(path: str) -> Dict[str, Dict[str, str]]:
    """Load emission factor rows from .csv with required columns."""
    # try UTF-8 first, then cp949 for common Korean Windows CSV encoding
    errors = []
    for enc in ("utf-8-sig", "cp949"):
        try:
            with open(path, "r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    raise ValueError("CSV header not found")
                missing = [c for c in REQUIRED_EF_COLUMNS if c not in reader.fieldnames]
                if missing:
                    raise ValueError(f"Missing required columns: {missing}")
                rows = [r for r in reader]
                return _build_ef_knowledge_from_rows(rows)
        except Exception as exc:
            errors.append(f"{enc}: {exc}")
    raise ValueError("CSV read failed. " + " | ".join(errors))


def load_ef_file(path: str) -> Dict[str, Dict[str, str]]:
    """Load EF data from .xlsx or .csv path."""
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return load_ef_csv(path)
    return load_ef_excel(path)


def required_uploads(stage: str) -> List[str]:
    """Return user-upload requirements per delivery stage."""
    stage = stage.lower()
    if stage == "ai_connection":
        return ["gemini_api_key", "gemini_model", "rate_limit_policy"]
    if stage == "knowledge_bootstrap":
        return [
            "emission_factor.xlsx|csv(Activity Name, Geography, Reference Product Name, Reference Product Unit)",
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
