from __future__ import annotations

import json

from qanalisa.ai.provider import AIProvider
from qanalisa.models import GeneratedTests, ImpactAnalysis, JiraIssue, StoryFacts


class TestGenerator:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    def generate(
        self,
        issue: JiraIssue,
        facts: StoryFacts,
        impact: ImpactAnalysis,
    ) -> GeneratedTests:
        context = {
            "issue": issue.model_dump(mode="json"),
            "story_facts": facts.model_dump(mode="json"),
            "impact_analysis": impact.model_dump(mode="json"),
        }
        prompt = """[STAGE:tests]
Gere uma matriz compacta e priorizada de testes de QA.
Use IDs CT01, CT02... e prioridades P0-P3.
Separe testes funcionais de negativos/borda.
Não invente pré-condições detalhadas nesta etapa; os casos ainda são compactos.
Regressões não confirmadas devem ser provenance=inferred.
Questões sem resposta no requisito devem permanecer como dúvidas, não como fatos.
Retorne somente os campos do schema solicitado.

CONTEXTO:
""" + json.dumps(context, ensure_ascii=False, indent=2)
        payload = self.provider.generate(prompt, GeneratedTests.model_json_schema())
        return GeneratedTests.model_validate(payload)
