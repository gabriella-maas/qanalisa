from qanalisa.models import (
    AnalysisMetadata,
    AnalysisResult,
    ErpImpact,
    JiraIssue,
    TestScenario as Scenario,
    TextItem,
)
from qanalisa.reports.markdown import render_markdown


def test_markdown_contains_approved_sections_and_provenance_markers():
    issue = JiraIssue(key="FN-14", title="Registrar desconto", description="Descrição")
    analysis = AnalysisResult(
        issue_key="FN-14",
        context="Contexto da tarefa",
        changes=[TextItem(text="Alteração explícita", provenance="story")],
        business_rules=[TextItem(text="Regra documentada", provenance="documented")],
        scope=[TextItem(text="Escopo manual", provenance="manual")],
        attention_points=[TextItem(text="Possível risco", provenance="inferred")],
        erp_impacts=[ErpImpact(module="Fiscal", reason="Pode refletir", provenance="inferred")],
        tests=[Scenario(id="CT01", title="Validar fluxo", priority="P0", provenance="story")],
        negative_tests=[Scenario(id="CT02", title="Validar ausência", priority="P1", provenance="inferred")],
        regression=[TextItem(text="Validar baixa", provenance="inferred")],
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
        "## 7. Cenários de teste",
        "## 8. Cenários negativos e de borda",
        "## 9. Regressivo sugerido",
        "## 10. Dúvidas / lacunas do requisito",
    ]:
        assert heading in text
    assert "✓" in text
    assert "★" in text
    assert "≈" in text
    assert "?" in text
    assert "[P0] CT01 — Validar fluxo" in text
    assert "Base VRSuper utilizada: v3" in text
