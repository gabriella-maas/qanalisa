from __future__ import annotations

import json

from qanalisa.ai.provider import AIProvider
from qanalisa.models import JiraIssue, StoryFacts


class StoryAnalyzer:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    def analyze(self, issue: JiraIssue) -> StoryFacts:
        prompt = """[STAGE:story]
Você é um analista de QA. Extraia APENAS o que está explícito no card do Jira.
Não invente regras, fluxos, módulos, resultados esperados ou dependências ausentes.
Itens comprovados pelo card devem usar provenance=story.
Quando algo estiver ausente, use provenance=unknown em um ponto de atenção/pergunta; não o apresente como fato.
Separe contexto, alterações, regras de negócio, escopo, pontos de atenção e dúvidas.
Retorne somente os campos do schema solicitado.

CARD:
""" + json.dumps(issue.model_dump(mode="json"), ensure_ascii=False, indent=2)
        payload = self.provider.generate(prompt, StoryFacts.model_json_schema())
        return StoryFacts.model_validate(payload)
