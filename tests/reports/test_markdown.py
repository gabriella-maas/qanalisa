from qanalisa.models import (
    AnalysisMetadata,
    AnalysisResult,
    ErpImpact,
    JiraIssue,
    TestScenario as Scenario,
    TextItem,
)
from qanalisa.reports.markdown import render_markdown


def test_markdown_separates_requirement_regression_and_exploratory_scenarios():
    issue = JiraIssue(key="FN-14", title="Registrar desconto", description="Descrição")
    analysis = AnalysisResult(
        issue_key="FN-14",
        context="Contexto da tarefa",
        changes=[TextItem(text="Alteração explícita", provenance="story")],
        business_rules=[TextItem(text="Regra documentada", provenance="documented")],
        scope=[TextItem(text="Escopo manual", provenance="manual")],
        attention_points=[TextItem(text="Possível risco", provenance="inferred")],
        erp_impacts=[ErpImpact(module="Fiscal", reason="Pode refletir", provenance="inferred")],
        tests=[
            Scenario(
                id="CT01",
                title="Validar fluxo",
                priority="P0",
                provenance="story",
                category="requirement",
            ),
            Scenario(
                id="CT02",
                title="Validar baixa",
                priority="P1",
                provenance="documented",
                category="regression",
            ),
        ],
        negative_tests=[
            Scenario(
                id="CT03",
                title="Validar ausência",
                priority="P1",
                provenance="inferred",
                category="exploratory",
            )
        ],
        regression=[TextItem(text="Validar liquidação", provenance="inferred")],
        questions=[TextItem(text="Confirmar comportamento", provenance="unknown")],
        metadata=AnalysisMetadata(
            generated_at="2026-09-17T10:00:00+00:00",
            provider="claude_cli",
            model="sonnet",
            knowledge_version=3,
        ),
    )

    text = render_markdown(issue, analysis)

    for heading in [
        "## 1. Contexto da tarefa",
        "## 2. O que está sendo alterado",
        "## 3. Regras de negócio identificadas",
        "## 4. Escopo da tarefa",
        "## 5. Pontos de atenção",
        "## 6. Impacto no ERP VRSuper",
        "## 7. Cenários obrigatórios",
        "## 8. Regressão sugerida",
        "## 9. Exploratórios / borda",
        "## 10. Dúvidas / lacunas do requisito",
    ]:
        assert heading in text
    assert "[P0] CT01 — Validar fluxo" in text
    assert "[P1] CT02 — Validar baixa" in text
    assert "[P1] CT03 — Validar ausência" in text
    assert text.index("CT01") < text.index("## 8. Regressão sugerida")
    assert text.index("CT02") > text.index("## 8. Regressão sugerida")
    assert text.index("CT03") > text.index("## 9. Exploratórios / borda")
    assert "Base VRSuper utilizada: v3" in text
