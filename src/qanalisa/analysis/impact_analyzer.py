from __future__ import annotations

import json

from qanalisa.ai.provider import AIProvider
from qanalisa.models import ImpactAnalysis, JiraIssue, KnowledgeMatch, StoryFacts


class ImpactAnalyzer:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    def analyze(
        self,
        issue: JiraIssue,
        facts: StoryFacts,
        knowledge: KnowledgeMatch,
    ) -> ImpactAnalysis:
        context = {
            "issue": issue.model_dump(mode="json"),
            "story_facts": facts.model_dump(mode="json"),
            "knowledge_match": knowledge.model_dump(mode="json"),
        }
        prompt = """[STAGE:impact]
Analise possíveis impactos de ERP usando SOMENTE os fatos da story e a base de conhecimento fornecida.
Preserve a proveniência: relações documented/manual continuam documented/manual.
Hipóteses e recomendações de regressão que não sejam fatos confirmados devem ser provenance=inferred.
Não transforme um relacionamento potencial em afirmação de que o módulo foi afetado.
Quando faltar informação para confirmar um impacto, trate-o como possibilidade de teste.
Retorne somente os campos do schema solicitado.

CONTEXTO:
""" + json.dumps(context, ensure_ascii=False, indent=2)
        payload = self.provider.generate(prompt, ImpactAnalysis.model_json_schema())
        return ImpactAnalysis.model_validate(payload)
