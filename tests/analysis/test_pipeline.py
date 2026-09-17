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
                "attention_points": [
                    {"text": "Confirmar nome do campo", "provenance": "story"}
                ],
                "module_candidates": ["Financeiro"],
                "feature_candidates": ["Conta a Pagar"],
                "questions": [
                    {"text": "Qual o nome do campo?", "provenance": "unknown"}
                ],
            }
        if "[STAGE:plan]" in prompt:
            self.stages.append("plan")
            return {
                "erp_impacts": [
                    {
                        "module": "Financeiro > Baixa de Título",
                        "reason": "Títulos de Contas a Pagar participam da baixa.",
                        "provenance": "documented",
                    }
                ],
                "attention_points": [
                    {"text": "Confirmar nome do campo", "provenance": "inferred"}
                ],
                "tests": [
                    {
                        "id": "CT01",
                        "title": "Validar fluxo principal",
                        "priority": "P0",
                        "provenance": "story",
                        "category": "requirement",
                        "related_risks": [],
                    },
                    {
                        "id": "CT02",
                        "title": "Validar baixa do título",
                        "priority": "P1",
                        "provenance": "documented",
                        "category": "regression",
                        "related_risks": [],
                    },
                ],
                "negative_tests": [
                    {
                        "id": "CT03",
                        "title": "Validar valor negativo",
                        "priority": "P2",
                        "provenance": "inferred",
                        "category": "exploratory",
                        "related_risks": [],
                    }
                ],
                "regression": [
                    {
                        "text": "Avaliar baixa do título após a alteração",
                        "provenance": "inferred",
                    }
                ],
                "questions": [
                    {"text": "Qual o nome do campo?", "provenance": "unknown"}
                ],
            }
        raise AssertionError("unexpected stage")


def test_pipeline_uses_two_ai_stages_deduplicates_and_preserves_categories():
    provider = StageProvider()
    progress_events = []
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

    result = pipeline.analyze(
        issue,
        knowledge,
        knowledge_version=3,
        progress=lambda stage, state, elapsed: progress_events.append((stage, state, elapsed)),
    )

    assert provider.stages == ["story", "plan"]
    assert [item.text for item in result.attention_points] == ["Confirmar nome do campo"]
    assert [item.text for item in result.questions] == ["Qual o nome do campo?"]
    assert result.tests[0].category == "requirement"
    assert result.tests[1].category == "regression"
    assert result.negative_tests[0].category == "exploratory"
    assert result.metadata.knowledge_version == 3
    assert [(stage, state) for stage, state, _ in progress_events] == [
        ("story", "start"),
        ("story", "done"),
        ("plan", "start"),
        ("plan", "done"),
    ]
