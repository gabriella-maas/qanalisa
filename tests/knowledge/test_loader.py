import json
from pathlib import Path

import yaml

from qanalisa.knowledge.loader import KnowledgeLoader


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_loader_preserves_version_and_documented_source(tmp_path: Path):
    _write_yaml(
        tmp_path / "modules.yaml",
        {
            "modules": [
                {
                    "name": "Financeiro",
                    "aliases": ["financeiro"],
                    "features": [
                        {
                            "name": "Conta a Pagar",
                            "aliases": ["conta a pagar", "contas a pagar"],
                            "keywords": ["título", "desconto"],
                            "source_type": "documented",
                            "source_ids": ["conta-pagar"],
                        }
                    ],
                }
            ]
        },
    )
    _write_yaml(tmp_path / "relationships.yaml", {"relationships": []})
    _write_yaml(tmp_path / "risks.yaml", {"risks": []})
    _write_yaml(tmp_path / "manual.yaml", {"relationships": [], "risks": []})
    _write_yaml(
        tmp_path / "sources.yaml",
        {
            "sources": [
                {
                    "id": "conta-pagar",
                    "title": "Consulta de Conta a Pagar",
                    "url": "https://docs.vrsoft.com.br/vrsuper/financeiro/conta-a-pagar/consulta-de-conta-a-pagar",
                }
            ]
        },
    )
    (tmp_path / "metadata.json").write_text(
        json.dumps({"knowledge_version": 3, "last_update": "2026-09-17"}),
        encoding="utf-8",
    )

    knowledge = KnowledgeLoader(tmp_path).load()

    assert knowledge.version == 3
    feature = knowledge.modules[0].features[0]
    assert feature.name == "Conta a Pagar"
    assert feature.source_type == "documented"
    assert feature.source_ids == ["conta-pagar"]


def test_seed_vrsuper_knowledge_contains_documented_financeiro_features():
    root = Path(__file__).resolve().parents[2] / "knowledge" / "vrsuper"

    knowledge = KnowledgeLoader(root).load()

    financeiro = next(module for module in knowledge.modules if module.name == "Financeiro")
    feature_names = {feature.name for feature in financeiro.features}
    assert "Conta a Pagar" in feature_names
    assert "Banco e Conta Corrente" in feature_names
    assert any(
        rel.from_feature == "Banco e Conta Corrente"
        and rel.to_feature == "Baixa de Título"
        and rel.provenance == "documented"
        for rel in knowledge.relationships
    )
