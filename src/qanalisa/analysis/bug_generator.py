from __future__ import annotations

import json

from qanalisa.ai.provider import AIProvider
from qanalisa.models import AnalysisResult, FullBugReport, JiraIssue, ShortBugReport


class BugGenerator:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    @staticmethod
    def _context(issue: JiraIssue, analysis: AnalysisResult, defect: str) -> str:
        return json.dumps(
            {
                "issue": issue.model_dump(mode="json"),
                "cached_analysis": analysis.model_dump(mode="json"),
                "defect_description": defect.strip(),
            },
            ensure_ascii=False,
            indent=2,
        )

    def generate_short(
        self,
        issue: JiraIssue,
        analysis: AnalysisResult,
        defect: str,
    ) -> ShortBugReport:
        prompt = """[STAGE:bug-short]
Gere um comentário curto e profissional de bug para colar no Jira.
Use somente o comportamento observado descrito pelo QA e o contexto salvo da tarefa.
Não invente passos, evidências, mensagens, status HTTP, valores ou condições que não apareçam no contexto.
Quando o resultado esperado vier da análise e não da observação, redija sem apresentá-lo como fato observado.
Seja direto: descreva ação, comportamento atual e consequência em um único texto curto.
Retorne somente os campos do schema solicitado.

CONTEXTO:
""" + self._context(issue, analysis, defect)
        payload = self.provider.generate(prompt, ShortBugReport.model_json_schema())
        return ShortBugReport.model_validate(payload)

    def generate_full(
        self,
        issue: JiraIssue,
        analysis: AnalysisResult,
        defect: str,
    ) -> FullBugReport:
        prompt = """[STAGE:bug-full]
Gere um bug report estruturado para QA com título, pré-condições, passos, resultado atual, resultado esperado, evidências e impacto.
Diferencie explicitamente o que foi observado pelo QA do que é inferido a partir da story/análise.
Não invente informações. Para pré-condições ou evidências ausentes, use exatamente "Não informado".
Os passos devem refletir somente ações descritas ou necessárias de forma segura para reproduzir o comportamento observado.
O resultado esperado pode ser inferido do requisito, mas não deve ser apresentado como observação.
Retorne somente os campos do schema solicitado.

CONTEXTO:
""" + self._context(issue, analysis, defect)
        payload = self.provider.generate(prompt, FullBugReport.model_json_schema())
        return FullBugReport.model_validate(payload)
