from __future__ import annotations

from dataclasses import replace
from typing import Optional

from mapping_engine import MappingEngine, MappingResult


class MappingPipeline:
    """Pipeline that separates deterministic engine and AI boundary decision."""

    def __init__(
        self,
        engine: MappingEngine,
        ai_resolver=None,
        registry=None,
        ai_threshold: float = 0.90,
    ):
        self.engine = engine
        self.ai_resolver = ai_resolver
        self.registry = registry
        self.ai_threshold = ai_threshold

    def map_activity(
        self,
        raw_name: str,
        source_type: str = "",
        geography_hint: str = "",
        unit_hint: str = "",
    ) -> MappingResult:
        if self.registry:
            approved = self.registry.get_approved_mapping(raw_name, geography_hint, unit_hint)
            if approved:
                return MappingResult(
                    status="exact",
                    selected_dataset=approved,
                    confidence=0.99,
                    review_required=False,
                    reason="Registry-approved mapping reused",
                    trace_log=["registry_hit=true", "ai_assist_called=false"],
                )
            memo = self.registry.get_memo_mapping(raw_name, geography_hint, unit_hint)
            if memo:
                return MappingResult(
                    status="exact",
                    selected_dataset=memo,
                    confidence=0.95,
                    review_required=False,
                    reason="Memoized deterministic mapping reused",
                    trace_log=["memo_hit=true", "ai_assist_called=false"],
                )

        deterministic = self.engine.map_activity(
            raw_name=raw_name,
            source_type=source_type,
            geography_hint=geography_hint,
            unit_hint=unit_hint,
        )

        has_candidate = deterministic.selected_dataset is not None
        if has_candidate and deterministic.confidence >= self.ai_threshold:
            if self.registry and deterministic.selected_dataset:
                self.registry.set_memo_mapping(raw_name, geography_hint, unit_hint, deterministic.selected_dataset)
            return deterministic

        if not self.ai_resolver:
            return deterministic

        normalized = self.engine.preprocess(raw_name)
        name_type = self.engine.classify_name_type(normalized)
        canonical = self.engine.canonicalize(normalized, name_type)
        candidates = self.engine.generate_candidates(canonical, geography_hint, unit_hint)

        payload = {
            "raw_name": raw_name,
            "source_type": source_type,
            "normalized_name": normalized,
            "canonical_hint": canonical,
            "geography_hint": geography_hint,
            "unit_hint": unit_hint,
            "search_top_n": candidates[:3],
            "deterministic_confidence": deterministic.confidence,
        }
        ai_response = self.ai_resolver.resolve(payload)
        proxy_candidates = ai_response.get("proxy_candidates", [])
        ai_selected = proxy_candidates[0] if proxy_candidates else None
        ai_confidence = float(ai_response.get("confidence", 0.0))
        ai_review_required = bool(ai_response.get("review_required", True))

        use_ai = (
            ai_selected is not None
            and (
                deterministic.selected_dataset is None
                or (ai_confidence > deterministic.confidence and ai_review_required <= deterministic.review_required)
            )
        )

        if not use_ai:
            return replace(
                deterministic,
                reason=f"{deterministic.reason} | AI consulted but deterministic kept",
                trace_log=deterministic.trace_log + ["decision_gate=ai_consulted_keep_deterministic", "ai_assist_called=true"],
            )

        return replace(
            deterministic,
            selected_dataset=ai_selected,
            confidence=ai_confidence,
            review_required=ai_review_required,
            reason=str(ai_response.get("reason", deterministic.reason)),
            trace_log=deterministic.trace_log + ["decision_gate=ai_needed", "ai_assist_called=true"],
        )
