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
        ctx = self.engine.analyze_activity(
            raw_name=raw_name,
            source_type=source_type,
            geography_hint=geography_hint,
            unit_hint=unit_hint,
        )
        deterministic = ctx.result

        if self.registry:
            approved = self.registry.get_approved_record(ctx.canonical_form, geography_hint, unit_hint)
            if approved:
                return MappingResult(
                    status=approved.status,
                    selected_dataset=approved.dataset,
                    confidence=approved.confidence,
                    review_required=False,
                    reason=f"Registry-approved mapping reused ({approved.approval_type})",
                    trace_log=[
                        "registry_hit=true",
                        f"approval_type={approved.approval_type}",
                        f"approved_by={approved.approved_by or 'unknown'}",
                        f"approved_reason={approved.reason or 'n/a'}",
                        "ai_assist_called=false",
                    ],
                )
            memo = self.registry.get_memo_record(ctx.canonical_form, geography_hint, unit_hint)
            if memo:
                return MappingResult(
                    status=memo.status,
                    selected_dataset=memo.dataset,
                    confidence=memo.confidence,
                    review_required=memo.review_required,
                    reason=f"Memoized mapping reused: {memo.reason or 'deterministic result'}",
                    trace_log=["memo_hit=true", "ai_assist_called=false"],
                )

        has_candidate = deterministic.selected_dataset is not None
        if has_candidate and deterministic.confidence >= self.ai_threshold:
            if self.registry and deterministic.selected_dataset:
                self.registry.set_memo_record(
                    canonical_form=ctx.canonical_form,
                    geography_hint=geography_hint,
                    unit_hint=unit_hint,
                    dataset=deterministic.selected_dataset,
                    status=deterministic.status,
                    confidence=deterministic.confidence,
                    review_required=deterministic.review_required,
                    reason=deterministic.reason,
                )
            return deterministic

        if not self.ai_resolver or not self._should_call_ai(ctx, deterministic):
            return deterministic

        payload = {
            "raw_name": raw_name,
            "source_type": source_type,
            "normalized_name": ctx.normalized_name,
            "canonical_hint": ctx.canonical_form,
            "geography_hint": geography_hint,
            "unit_hint": unit_hint,
            "search_top_n": ctx.candidates[:3],
            "deterministic_confidence": deterministic.confidence,
        }
        ai_response = self.ai_resolver.resolve(payload)
        ai_source = str(ai_response.get("source", "gemini_live"))
        proxy_candidates = ai_response.get("proxy_candidates", [])
        ai_selected = proxy_candidates[0] if proxy_candidates else None
        ai_confidence = float(ai_response.get("confidence", 0.0))
        ai_review_required = bool(ai_response.get("review_required", True))

        use_ai = self._can_replace_deterministic(
            deterministic_selected=deterministic.selected_dataset,
            deterministic_confidence=deterministic.confidence,
            deterministic_review=deterministic.review_required,
            ai_selected=ai_selected,
            ai_confidence=ai_confidence,
            ai_review=ai_review_required,
        )

        if not use_ai:
            return replace(
                deterministic,
                reason=f"{deterministic.reason} | AI consulted but deterministic kept",
                trace_log=deterministic.trace_log
                + ["decision_gate=ai_consulted_keep_deterministic", "ai_assist_called=true", f"ai_source={ai_source}"],
            )

        return replace(
            deterministic,
            selected_dataset=ai_selected,
            confidence=ai_confidence,
            review_required=ai_review_required,
            reason=str(ai_response.get("reason", deterministic.reason)),
            trace_log=deterministic.trace_log + ["decision_gate=ai_needed", "ai_assist_called=true", f"ai_source={ai_source}"],
        )

    @staticmethod
    def _can_replace_deterministic(
        deterministic_selected,
        deterministic_confidence: float,
        deterministic_review: bool,
        ai_selected,
        ai_confidence: float,
        ai_review: bool,
    ) -> bool:
        if ai_selected is None:
            return False
        if deterministic_selected is None:
            return True
        return ai_confidence > deterministic_confidence and ai_review <= deterministic_review

    def _should_call_ai(self, ctx, deterministic: MappingResult) -> bool:
        if ctx.name_type in {"energy", "wastewater"}:
            return False
        if ctx.candidate_source in {"catalog_exact", "ef_exact"}:
            return False
        if deterministic.selected_dataset is None:
            return True
        return deterministic.confidence < self.ai_threshold
