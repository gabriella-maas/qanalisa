from __future__ import annotations

import re
import unicodedata

from qanalisa.models import ErpImpact, Provenance, TestScenario, TextItem

_PROVENANCE_RANK: dict[Provenance, int] = {
    "story": 5,
    "documented": 4,
    "manual": 3,
    "inferred": 2,
    "unknown": 1,
}


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def dedupe_text_items(items: list[TextItem]) -> list[TextItem]:
    chosen: dict[str, TextItem] = {}
    order: list[str] = []
    for item in items:
        key = normalize_text(item.text)
        if not key:
            continue
        current = chosen.get(key)
        if current is None:
            chosen[key] = item
            order.append(key)
        elif _PROVENANCE_RANK[item.provenance] > _PROVENANCE_RANK[current.provenance]:
            chosen[key] = item
    return [chosen[key] for key in order]


def dedupe_impacts(items: list[ErpImpact]) -> list[ErpImpact]:
    chosen: dict[str, ErpImpact] = {}
    order: list[str] = []
    for item in items:
        key = f"{normalize_text(item.module)}|{normalize_text(item.reason)}"
        current = chosen.get(key)
        if current is None:
            chosen[key] = item
            order.append(key)
        elif _PROVENANCE_RANK[item.provenance] > _PROVENANCE_RANK[current.provenance]:
            chosen[key] = item
    return [chosen[key] for key in order]


def dedupe_scenarios(
    items: list[TestScenario],
    *,
    seen_titles: set[str] | None = None,
) -> tuple[list[TestScenario], set[str]]:
    seen = set() if seen_titles is None else set(seen_titles)
    result: list[TestScenario] = []
    for item in items:
        key = normalize_text(item.title)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result, seen
