from __future__ import annotations

import json

from qanalisa.ai.provider import AIProvider
from qanalisa.models import AnalysisResult, DetailedTestCase, JiraIssue, TestScenario


class ScenarioNotFoundError(RuntimeError):
    """Raised when a compact scenario is absent from cached analysis."""


class ScenarioExpander:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    @staticmethod
    def _find(analysis: AnalysisResult, scenario_id: str) -> TestScenario:
        wanted = scenario_id.upper()
        for scenario in [*analysis.tests, *analysis.negative_tests]:
            if scenario.id.upper() == wanted:
                return scenario
        raise ScenarioNotFoundError(
            f"Scenario {wanted} was not found in the cached analysis."
        )

    def expand(
        self,
        issue: JiraIssue,
        analysis: AnalysisResult,
        scenario_id: str,
    ) -> DetailedTestCase:
        scenario = self._find(analysis, scenario_id)
        context = {
            "issue": issue.model_dump(mode="json"),
            "cached_analysis": analysis.model_dump(mode="json"),
            "scenario": scenario.model_dump(mode="json"),
        }
        prompt = """[STAGE:scenario]
Detalhe SOMENTE o cenário selecionado com base na story e na análise em cache.
Não invente dados específicos, cadastros, permissões ou valores que não estejam no contexto.
Quando uma pré-condição não puder ser afirmada como fato, descreva-a de forma genérica e necessária ao fluxo.
Forneça objetivo, pré-condições, passos, resultado esperado e riscos relacionados.
Retorne somente os campos do schema solicitado.

CONTEXTO:
""" + json.dumps(context, ensure_ascii=False, indent=2)
        payload = self.provider.generate(prompt, DetailedTestCase.model_json_schema())
        detailed = DetailedTestCase.model_validate(payload)
        return detailed.model_copy(
            update={
                "id": scenario.id,
                "title": scenario.title,
                "priority": scenario.priority,
            }
        )
