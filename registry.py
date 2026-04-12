from __future__ import annotations

from typing import Dict, Optional, Tuple


class MappingRegistry:
    """In-memory registry/cache.

    - approved: human-approved long-term mappings
    - memo: session-level deterministic reuse cache
    - ai_cache: payload-based AI response cache
    """

    def __init__(self):
        self._approved: Dict[Tuple[str, str, str], str] = {}
        self._memo: Dict[Tuple[str, str, str], str] = {}
        self._ai_cache: Dict[str, dict] = {}

    @staticmethod
    def _norm(text: str) -> str:
        return (text or "").strip().lower()

    def make_activity_key(self, raw_name: str, geography_hint: str = "", unit_hint: str = "") -> Tuple[str, str, str]:
        return (self._norm(raw_name), self._norm(geography_hint), self._norm(unit_hint))

    def get_approved_mapping(self, raw_name: str, geography_hint: str = "", unit_hint: str = "") -> Optional[str]:
        return self._approved.get(self.make_activity_key(raw_name, geography_hint, unit_hint))

    def set_approved_mapping(self, raw_name: str, geography_hint: str, unit_hint: str, dataset: str) -> None:
        self._approved[self.make_activity_key(raw_name, geography_hint, unit_hint)] = dataset

    def get_memo_mapping(self, raw_name: str, geography_hint: str = "", unit_hint: str = "") -> Optional[str]:
        return self._memo.get(self.make_activity_key(raw_name, geography_hint, unit_hint))

    def set_memo_mapping(self, raw_name: str, geography_hint: str, unit_hint: str, dataset: str) -> None:
        self._memo[self.make_activity_key(raw_name, geography_hint, unit_hint)] = dataset

    def get_ai_cache(self, payload_key: str) -> Optional[dict]:
        return self._ai_cache.get(payload_key)

    def set_ai_cache(self, payload_key: str, response: dict) -> None:
        self._ai_cache[payload_key] = response
