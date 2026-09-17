import pytest

from qanalisa.analysis.scenario_expander import ScenarioExpander, ScenarioNotFoundError
from qanalisa.models import AnalysisMetadata, AnalysisResult, JiraIssue, TestScenario as Scenario


class FakeProvider:
    def __init__(self):
        self.calls = 0
        self.prompt = ""

    def generate(self, prompt: str, schema: dict) -> dict:
        self.calls += 1
        self.prompt = prompt
        return {
            "id": "CT07",
            "title": "Consultar contrato após inativação",
            "priority": "P3",
            "objective": "Validar que a consulta se mantém consistente após a inativação.",
            "preconditions": ["Existe um contrato ativo cadastrado."],
            "steps": ["Inativar o contrato.", "Consultar contratos pelo período."],
            "expected_result": "A consulta deve responder sem erro e respeitar a situação do contrato.",
            "related_risks": ["Falha HTTP 500 na consulta por período."],
        }


def _analysis() -> AnalysisResult:
    return AnalysisResult(
        issue_key="FN-14",
        context="Inativação de contrato",
        tests=[
            Scenario(
                id="CT07",
                title="Consultar contrato após inativação",
                priority="P1",
                provenance="inferred",
                related_risks=["consulta por período"],
            )
        ],
        metadata=AnalysisMetadata(
            generated_at="2026-09-17T10:00:00+00:00",
            provider="claude_cli",
            knowledge_version=1,
        ),
    )


def test_expands_existing_scenario_and_preserves_original_priority():
    provider = FakeProvider()
    expander = ScenarioExpander(provider)
    issue = JiraIssue(key="FN-14", title="Contrato", description="Descrição")

    detailed = expander.expand(issue, _analysis(), "ct07")

    assert detailed.id == "CT07"
    assert detailed.priority == "P1"
    assert detailed.steps == ["Inativar o contrato.", "Consultar contratos pelo período."]
    assert detailed.expected_result.startswith("A consulta")
    assert "[STAGE:scenario]" in provider.prompt
    assert provider.calls == 1


def test_unknown_scenario_does_not_call_provider():
    provider = FakeProvider()
    expander = ScenarioExpander(provider)
    issue = JiraIssue(key="FN-14", title="Contrato", description="Descrição")

    with pytest.raises(
        ScenarioNotFoundError,
        match="Scenario CT99 was not found in the cached analysis\\.",
    ):
        expander.expand(issue, _analysis(), "CT99")

    assert provider.calls == 0
