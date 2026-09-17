from __future__ import annotations

import json
from pathlib import Path

import yaml

from qanalisa.models import (
    KnowledgeBase,
    KnowledgeModule,
    KnowledgeRelationship,
    KnowledgeRisk,
    KnowledgeSource,
)


class KnowledgeLoader:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _yaml(self, name: str) -> dict:
        path = self.root / name
        if not path.exists():
            return {}
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def load(self) -> KnowledgeBase:
        metadata_path = self.root / "metadata.json"
        metadata = (
            json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata_path.exists()
            else {"knowledge_version": 1}
        )

        modules_data = self._yaml("modules.yaml").get("modules", [])
        relationships_data = self._yaml("relationships.yaml").get("relationships", [])
        risks_data = self._yaml("risks.yaml").get("risks", [])
        manual = self._yaml("manual.yaml")
        sources_data = self._yaml("sources.yaml").get("sources", [])

        relationships_data = [*relationships_data, *manual.get("relationships", [])]
        risks_data = [*risks_data, *manual.get("risks", [])]

        return KnowledgeBase(
            version=int(metadata.get("knowledge_version", 1)),
            last_update=metadata.get("last_update"),
            modules=[KnowledgeModule.model_validate(item) for item in modules_data],
            relationships=[
                KnowledgeRelationship.model_validate(item) for item in relationships_data
            ],
            risks=[KnowledgeRisk.model_validate(item) for item in risks_data],
            sources=[KnowledgeSource.model_validate(item) for item in sources_data],
        )
