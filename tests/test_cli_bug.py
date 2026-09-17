from pathlib import Path

from typer.testing import CliRunner

import qanalisa.cli as cli
from qanalisa.models import AnalysisMetadata, AnalysisResult, JiraIssue
from qanalisa.storage.workspace import Workspace

runner = CliRunner()


class FakeSettings:
    jira_base_url = "https://example.atlassian.net"
    jira_email = "qa@example.com"
    jira_api_token = "secret"
    ai_provider = "claude_cli"
    claude_command = "claude"
    claude_model = "sonnet"
    claude_timeout_seconds = 120


class FakeProvider:
    def __init__(self, *args, **kwargs):
        pass

    def preflight(self):
        return []

    def generate(self, prompt, schema):
        if "[STAGE:bug-short]" in prompt:
            return {
                "text": "Ao inativar o contrato, a consulta por período passa a retornar HTTP 500."
            }
        if "[STAGE:bug-full]" in prompt:
            return {
                "title": "Consulta retorna HTTP 500 após inativação",
                "preconditions": ["Não informado"],
                "steps": ["Inativar o contrato.", "Consultar por período."],
                "actual_result": "A consulta retorna HTTP 500.",
                "expected_result": "A consulta deve ser concluída sem erro.",
                "evidence": ["Não informado"],
                "impact": "Impede consultas por período após a inativação.",
            }
        raise AssertionError("unexpected prompt")


def _seed(tmp_path: Path):
    ws = Workspace(tmp_path / ".qa")
    ws.save_story(JiraIssue(key="FN-14", title="Inativar contrato", description="Descrição"))
    ws.save_analysis(
        "FN-14",
        AnalysisResult(
            issue_key="FN-14",
            context="Contexto",
            metadata=AnalysisMetadata(
                generated_at="2026-09-17T10:00:00+00:00",
                provider="claude_cli",
                knowledge_version=1,
            ),
        ),
    )


def _patch(tmp_path: Path, monkeypatch):
    _seed(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "Settings", lambda: FakeSettings())
    monkeypatch.setattr(cli, "ClaudeCliProvider", FakeProvider)


def test_bug_cli_short_prints_jira_ready_body(tmp_path: Path, monkeypatch):
    _patch(tmp_path, monkeypatch)

    result = runner.invoke(
        cli.app,
        ["bug", "FN-14"],
        input="inativei o contrato e a consulta por período retornou 500\n",
    )

    assert result.exit_code == 0, result.output
    assert "Ao inativar o contrato, a consulta por período passa a retornar HTTP 500." in result.output
    assert "## Resultado atual" not in result.output
    assert len(list((tmp_path / ".qa" / "FN-14" / "bugs").glob("bug-*.md"))) == 1


def test_bug_cli_full_prints_structured_report(tmp_path: Path, monkeypatch):
    _patch(tmp_path, monkeypatch)

    result = runner.invoke(
        cli.app,
        ["bug", "FN-14", "--full"],
        input="inativei o contrato e a consulta por período retornou 500\n",
    )

    assert result.exit_code == 0, result.output
    assert "Consulta retorna HTTP 500 após inativação" in result.output
    assert "Pré-condições" in result.output
    assert "Resultado atual" in result.output
    assert "Resultado esperado" in result.output
    assert "Evidências" in result.output
    assert "Impacto" in result.output


def test_bug_cli_requires_cached_story_and_analysis(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(cli.app, ["bug", "FN-14"], input="erro\n")

    assert result.exit_code == 1
    assert "Execute qanalisa FN-14 primeiro" in result.output
