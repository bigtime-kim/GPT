from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class ApprovedRecord:
    dataset: str
    status: str
    confidence: float
    approval_type: str = "human"
    approved_by: str = ""
    approved_at: str = ""
    reason: str = ""


@dataclass
class MemoRecord:
    dataset: str
    status: str
    confidence: float
    review_required: bool
    reason: str = ""


class MappingRegistry:
    """In-memory registry/cache.

    - approved: human-approved long-term mappings
    - memo: session-level deterministic reuse cache
    - ai_cache: payload-based AI response cache
    """

    def __init__(self):
        self._approved: Dict[Tuple[str, str, str], ApprovedRecord] = {}
        self._memo: Dict[Tuple[str, str, str], MemoRecord] = {}
        self._ai_cache: Dict[str, dict] = {}

    @staticmethod
    def _norm(text: str) -> str:
        return (text or "").strip().lower()

    def make_activity_key(self, raw_name: str, geography_hint: str = "", unit_hint: str = "") -> Tuple[str, str, str]:
        return (self._norm(raw_name), self._norm(geography_hint), self._norm(unit_hint))

    def make_canonical_key(self, canonical_form: str, geography_hint: str = "", unit_hint: str = "") -> Tuple[str, str, str]:
        return (self._norm(canonical_form), self._norm(geography_hint), self._norm(unit_hint))

    def get_approved_record(self, canonical_form: str, geography_hint: str = "", unit_hint: str = "") -> Optional[ApprovedRecord]:
        return self._approved.get(self.make_canonical_key(canonical_form, geography_hint, unit_hint))

    def set_approved_record(
        self,
        canonical_form: str,
        geography_hint: str,
        unit_hint: str,
        dataset: str,
        status: str,
        confidence: float,
        approval_type: str = "human",
        approved_by: str = "",
        approved_at: str = "",
        reason: str = "",
    ) -> None:
        self._approved[self.make_canonical_key(canonical_form, geography_hint, unit_hint)] = ApprovedRecord(
            dataset=dataset,
            status=status,
            confidence=confidence,
            approval_type=approval_type,
            approved_by=approved_by,
            approved_at=approved_at,
            reason=reason,
        )

    # Deprecated legacy method for raw-name based access.
    def get_approved_mapping(self, raw_name: str, geography_hint: str = "", unit_hint: str = "") -> Optional[str]:
        raise NotImplementedError("Use get_approved_record(canonical_form, geography_hint, unit_hint)")

    def set_approved_mapping(self, raw_name: str, geography_hint: str, unit_hint: str, dataset: str) -> None:
        raise NotImplementedError("Use set_approved_record with canonical_form + metadata")

    def get_memo_record(self, canonical_form: str, geography_hint: str = "", unit_hint: str = "") -> Optional[MemoRecord]:
        return self._memo.get(self.make_canonical_key(canonical_form, geography_hint, unit_hint))

    def set_memo_record(
        self,
        canonical_form: str,
        geography_hint: str,
        unit_hint: str,
        dataset: str,
        status: str,
        confidence: float,
        review_required: bool,
        reason: str = "",
    ) -> None:
        self._memo[self.make_canonical_key(canonical_form, geography_hint, unit_hint)] = MemoRecord(
            dataset=dataset,
            status=status,
            confidence=confidence,
            review_required=review_required,
            reason=reason,
        )

    def get_ai_cache(self, payload_key: str) -> Optional[dict]:
        return self._ai_cache.get(payload_key)

    def set_ai_cache(self, payload_key: str, response: dict) -> None:
        self._ai_cache[payload_key] = response
