from qanalisa.analysis.pipeline import AnalysisPipeline
from qanalisa.models import (
    JiraIssue,
    KnowledgeMatch,
    KnowledgeRelationship,
    KnowledgeRisk,
)


class StageProvider:
    def __init__(self):
        self.stages = []

    def generate(self, prompt: str, schema: dict) -> dict:
        if "[STAGE:story]" in prompt:
            self.stages.append("story")
            return {
                "context": "Alterar título financeiro",
                "changes": [{"text": "Alterar campo financeiro", "provenance": "story"}],
                "business_rules": [],
                "scope": [],
                "attention_points": [],
                "module_candidates": ["Financeiro"],
                "feature_candidates": ["Conta a Pagar"],
                "questions": [],
            }
        if "[STAGE:impact]" in prompt:
            self.stages.append("impact")
            return {
                "erp_impacts": [
                    {
                        "module": "Financeiro",
                        "reason": "Relacionamento documentado com Baixa de Título",
                        "provenance": "documented",
                    }
                ],
                "regression": [
                    {
                        "text": "Avaliar baixa do título após a alteração",
                        "provenance": "inferred",
                    }
                ],
                "attention_points": [],
            }
        if "[STAGE:tests]" in prompt:
            self.stages.append("tests")
            return {
                "tests": [
                    {
                        "id": "CT01",
                        "title": "Validar fluxo principal",
                        "priority": "P0",
                        "provenance": "story",
                        "related_risks": [],
                    }
                ],
                "negative_tests": [],
                "regression": [
                    {
                        "text": "Avaliar baixa do título após a alteração",
                        "provenance": "inferred",
                    }
                ],
                "questions": [],
            }
        raise AssertionError("unexpected stage")


def test_pipeline_preserves_stage_order_and_provenance():
    provider = StageProvider()
    pipeline = AnalysisPipeline(provider, provider_name="claude_cli", model="sonnet")
    issue = JiraIssue(key="FN-14", title="Teste", description="Descrição")
    knowledge = KnowledgeMatch(
        module="Financeiro",
        feature="Conta a Pagar",
        confidence=0.9,
        relationships=[
            KnowledgeRelationship(
                from_module="Financeiro",
                from_feature="Conta a Pagar",
                to_module="Financeiro",
                to_feature="Baixa de Título",
                reason="Relação documentada",
                provenance="documented",
            )
        ],
        risks=[
            KnowledgeRisk(
                module="Financeiro",
                feature="Conta a Pagar",
                text="Risco documentado",
                provenance="documented",
            )
        ],
    )

    result = pipeline.analyze(issue, knowledge, knowledge_version=3)

    assert provider.stages == ["story", "impact", "tests"]
    assert result.erp_impacts[0].provenance == "documented"
    assert result.regression[0].provenance == "inferred"
    assert result.tests[0].id == "CT01"
    assert result.metadata.knowledge_version == 3
    assert result.metadata.provider == "claude_cli"
