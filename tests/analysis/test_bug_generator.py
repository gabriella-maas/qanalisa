from qanalisa.analysis.bug_generator import BugGenerator
from qanalisa.models import AnalysisMetadata, AnalysisResult, JiraIssue, TextItem


class FakeProvider:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str, schema: dict) -> dict:
        self.prompts.append(prompt)
        if "[STAGE:bug-short]" in prompt:
            return {
                "text": (
                    "Ao inativar o contrato, o sistema exibe a confirmação de sucesso, "
                    "porém a consulta por período passa a retornar HTTP 500."
                )
            }
        if "[STAGE:bug-full]" in prompt:
            return {
                "title": "Consulta por período retorna HTTP 500 após inativar contrato",
                "preconditions": ["Não informado"],
                "steps": [
                    "Inativar o contrato.",
                    "Realizar a consulta por período.",
                ],
                "actual_result": "A consulta por período retorna HTTP 500.",
                "expected_result": "A consulta por período deve ser concluída sem erro.",
                "evidence": ["Não informado"],
                "impact": "A consulta por período fica indisponível após a inativação.",
            }
        raise AssertionError("unexpected prompt")


def _context():
    issue = JiraIssue(
        key="FN-14",
        title="Inativar contrato",
        description="Permitir a inativação de contratos.",
    )
    analysis = AnalysisResult(
        issue_key="FN-14",
        context="Fluxo de inativação de contrato",
        regression=[TextItem(text="Validar consulta após inativação", provenance="inferred")],
        metadata=AnalysisMetadata(
            generated_at="2026-09-17T10:00:00+00:00",
            provider="claude_cli",
            knowledge_version=1,
        ),
    )
    return issue, analysis


def test_generate_short_bug_report_is_concise_and_grounded():
    provider = FakeProvider()
    generator = BugGenerator(provider)
    issue, analysis = _context()

    report = generator.generate_short(
        issue,
        analysis,
        "inativei o contrato, mostrou sucesso, depois consulta por período retornou 500",
    )

    assert report.text.startswith("Ao inativar o contrato")
    assert "HTTP 500" in report.text
    assert "[STAGE:bug-short]" in provider.prompts[0]
    assert "não invente" in provider.prompts[0].lower()


def test_generate_full_bug_report_marks_unknowns_instead_of_fabricating():
    provider = FakeProvider()
    generator = BugGenerator(provider)
    issue, analysis = _context()

    report = generator.generate_full(
        issue,
        analysis,
        "inativei o contrato, mostrou sucesso, depois consulta por período retornou 500",
    )

    assert report.title
    assert report.preconditions == ["Não informado"]
    assert report.steps == ["Inativar o contrato.", "Realizar a consulta por período."]
    assert report.actual_result == "A consulta por período retorna HTTP 500."
    assert report.expected_result
    assert report.evidence == ["Não informado"]
    assert report.impact
    assert "observado" in provider.prompts[0].lower()
    assert "inferido" in provider.prompts[0].lower()
