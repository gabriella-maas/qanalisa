from __future__ import annotations

import re
import unicodedata

from qanalisa.models import KnowledgeBase, KnowledgeMatch


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", normalized).strip()


class KnowledgeMatcher:
    def __init__(self, knowledge: KnowledgeBase) -> None:
        self.knowledge = knowledge

    def match(self, text: str) -> KnowledgeMatch:
        haystack = _normalize(text)
        best_module = None
        best_feature = None
        best_score = 0.0

        for module in self.knowledge.modules:
            module_terms = [module.name, *module.aliases]
            module_hits = sum(1 for term in module_terms if _normalize(term) in haystack)

            for feature in module.features:
                aliases = [feature.name, *feature.aliases]
                alias_hits = sum(1 for term in aliases if _normalize(term) in haystack)
                keyword_hits = sum(1 for term in feature.keywords if _normalize(term) in haystack)

                # Exact feature aliases carry most weight; module/keywords reinforce the match.
                score = min(1.0, alias_hits * 0.6 + module_hits * 0.2 + keyword_hits * 0.1)
                if score > best_score:
                    best_score = score
                    best_module = module.name
                    best_feature = feature.name

            if not module.features and module_hits:
                score = min(1.0, module_hits * 0.5)
                if score > best_score:
                    best_score = score
                    best_module = module.name
                    best_feature = None

        if best_score == 0.0 or best_module is None:
            return KnowledgeMatch()

        relationships = [
            rel
            for rel in self.knowledge.relationships
            if rel.from_module == best_module
            and (rel.from_feature is None or rel.from_feature == best_feature)
        ]
        risks = [
            risk
            for risk in self.knowledge.risks
            if risk.module == best_module
            and (risk.feature is None or risk.feature == best_feature)
        ]
        return KnowledgeMatch(
            module=best_module,
            feature=best_feature,
            confidence=round(best_score, 3),
            relationships=relationships,
            risks=risks,
        )
