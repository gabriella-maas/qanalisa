from pathlib import Path

from typer.testing import CliRunner

import qanalisa.cli as cli
from qanalisa.models import AnalysisMetadata, AnalysisResult, JiraIssue, TestScenario as Scenario
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
    calls = 0

    def __init__(self, *args, **kwargs):
        pass

    def preflight(self):
        return []

    def generate(self, prompt, schema):
        type(self).calls += 1
        return {
            "id": "CT07",
            "title": "Consultar contrato após inativação",
            "priority": "P0",
            "objective": "Validar consulta após inativação.",
            "preconditions": ["Contrato ativo existente."],
            "steps": ["Inativar contrato.", "Consultar por período."],
            "expected_result": "Consulta concluída sem erro.",
            "related_risks": ["Erro 500"],
        }


def _seed(tmp_path: Path):
    ws = Workspace(tmp_path / ".qa")
    ws.save_story(JiraIssue(key="FN-14", title="Contrato", description="Descrição"))
    ws.save_analysis(
        "FN-14",
        AnalysisResult(
            issue_key="FN-14",
            context="Contexto",
            tests=[Scenario(id="CT07", title="Consultar após inativação", priority="P1")],
            metadata=AnalysisMetadata(
                generated_at="2026-09-17T10:00:00+00:00",
                provider="claude_cli",
                knowledge_version=1,
            ),
        ),
    )


def test_cli_expands_cached_scenario_without_fetching_jira(tmp_path: Path, monkeypatch):
    _seed(tmp_path)
    FakeProvider.calls = 0
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "Settings", lambda: FakeSettings())
    monkeypatch.setattr(cli, "ClaudeCliProvider", FakeProvider)

    class JiraMustNotBeCalled:
        def __init__(self, *args, **kwargs):
            raise AssertionError("Jira must not be called when expanding cached scenario")

    monkeypatch.setattr(cli, "JiraClient", JiraMustNotBeCalled)

    result = runner.invoke(cli.app, ["FN-14", "--test", "CT07"])

    assert result.exit_code == 0, result.stdout
    assert "CT07" in result.stdout
    assert "Prioridade: P1" in result.stdout
    assert "Inativar contrato." in result.stdout
    assert FakeProvider.calls == 1


def test_cli_unknown_scenario_is_user_facing(tmp_path: Path, monkeypatch):
    _seed(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "Settings", lambda: FakeSettings())
    monkeypatch.setattr(cli, "ClaudeCliProvider", FakeProvider)

    result = runner.invoke(cli.app, ["FN-14", "--test", "CT99"])

    assert result.exit_code == 1
    assert "Scenario CT99 was not found in the cached analysis." in result.output
