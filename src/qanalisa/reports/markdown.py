from __future__ import annotations

from qanalisa.models import AnalysisResult, JiraIssue, Provenance, TestScenario, TextItem

_MARKERS: dict[Provenance, str] = {
    "story": "✓",
    "documented": "✓",
    "manual": "★",
    "inferred": "≈",
    "unknown": "?",
}


def _items(items: list[TextItem]) -> str:
    if not items:
        return "_Nenhum item identificado._"
    return "\n".join(f"- {_MARKERS[item.provenance]} {item.text}" for item in items)


def _scenarios(items: list[TestScenario]) -> str:
    if not items:
        return "_Nenhum cenário identificado._"
    return "\n".join(
        f"- [{item.priority}] {item.id} — {item.title} {_MARKERS[item.provenance]}"
        for item in items
    )


def render_markdown(issue: JiraIssue, analysis: AnalysisResult) -> str:
    impacts = (
        "\n".join(
            f"- {_MARKERS[item.provenance]} **{item.module}** — {item.reason}"
            for item in analysis.erp_impacts
        )
        if analysis.erp_impacts
        else "_Nenhum impacto de ERP identificado._"
    )

    return f"""# {issue.key} — {issue.title}

## 1. Contexto da tarefa

{analysis.context}

## 2. O que está sendo alterado

{_items(analysis.changes)}

## 3. Regras de negócio identificadas

{_items(analysis.business_rules)}

## 4. Escopo da tarefa

{_items(analysis.scope)}

## 5. Pontos de atenção

{_items(analysis.attention_points)}

## 6. Impacto no ERP VRSuper

{impacts}

## 7. Cenários de teste

{_scenarios(analysis.tests)}

## 8. Cenários negativos e de borda

{_scenarios(analysis.negative_tests)}

## 9. Regressivo sugerido

{_items(analysis.regression)}

## 10. Dúvidas / lacunas do requisito

{_items(analysis.questions)}

---

Base VRSuper utilizada: v{analysis.metadata.knowledge_version}  
Gerado em: {analysis.metadata.generated_at}  
Provedor: {analysis.metadata.provider}  
Modelo: {analysis.metadata.model or "padrão da assinatura"}

Legenda: ✓ story/documentado · ★ conhecimento manual · ≈ inferência · ? necessita confirmação
"""
