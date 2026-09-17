from __future__ import annotations

import json

from qanalisa.ai.provider import AIProvider
from qanalisa.models import JiraIssue, KnowledgeMatch, PlanAnalysis, StoryFacts


class PlanAnalyzer:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    def analyze(
        self,
        issue: JiraIssue,
        facts: StoryFacts,
        knowledge: KnowledgeMatch,
    ) -> PlanAnalysis:
        context = {
            "issue": issue.model_dump(mode="json"),
            "story_facts": facts.model_dump(mode="json"),
            "knowledge_match": knowledge.model_dump(mode="json"),
        }
        prompt = """[STAGE:plan]
Você é um analista sênior de QA especializado em ERP. Gere, em UMA ÚNICA análise, impactos de ERP, regressão e matriz compacta de testes.

REGRAS DE CONFIANÇA:
- Use somente os fatos extraídos da story e a base de conhecimento fornecida.
- Preserve provenance: story=documentado no card; documented=fonte oficial VRSuper; manual=conhecimento manual; inferred=hipótese de QA; unknown=sem confirmação.
- Nunca transforme uma possibilidade em impacto confirmado.
- Relações da knowledge base podem justificar regressão, mas não viram requisito da story.

CATEGORIAS DE CENÁRIO:
- category=requirement: comportamento explicitamente exigido pela story/critério de aceite. Em regra, provenance=story.
- category=regression: validação de fluxo relacionado por knowledge base ou possível efeito colateral.
- category=exploratory: borda, negativo ou investigação não especificada no requisito.
- Todos os negative_tests devem usar category=exploratory.

QUALIDADE:
- Use IDs CT01, CT02... e prioridades P0-P3.
- Evite cenários semanticamente duplicados e variações que validem a mesma regra sem ganho real.
- Prefira uma matriz enxuta e priorizada.
- Não invente pré-condições detalhadas nesta etapa.
- Questões sem resposta continuam como dúvidas.
- Retorne somente os campos do schema solicitado.

CONTEXTO:
""" + json.dumps(context, ensure_ascii=False, indent=2)
        payload = self.provider.generate(prompt, PlanAnalysis.model_json_schema())
        return PlanAnalysis.model_validate(payload)
