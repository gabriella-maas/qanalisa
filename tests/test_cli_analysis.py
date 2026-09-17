from pathlib import Path

from typer.testing import CliRunner

import qanalisa.cli as cli
from qanalisa.models import KnowledgeBase, KnowledgeFeature, KnowledgeModule

runner = CliRunner()


class FakeSettings:
    jira_base_url = "https://example.atlassian.net"
    jira_email = "qa@example.com"
    jira_api_token = "secret"
    ai_provider = "claude_cli"
    claude_command = "claude"
    claude_model = "sonnet"
    claude_timeout_seconds = 120


class FakeJiraClient:
    calls = 0

    def __init__(self, *args, **kwargs):
        pass

    def get_issue(self, issue_key):
        from qanalisa.models import JiraIssue

        type(self).calls += 1
        return JiraIssue(
            key=issue_key,
            title="Registrar desconto",
            description="Registrar desconto no Contas a Pagar.",
        )


class FakeProvider:
    calls = 0

    def __init__(self, *args, **kwargs):
        pass

    def preflight(self):
        return []

    def generate(self, prompt, schema):
        type(self).calls += 1
        if "[STAGE:story]" in prompt:
            return {
                "context": "Registrar desconto",
                "changes": [{"text": "Registrar desconto", "provenance": "story"}],
                "business_rules": [],
                "scope": [],
                "attention_points": [],
                "module_candidates": ["Financeiro"],
                "feature_candidates": ["Conta a Pagar"],
                "questions": [],
            }
        if "[STAGE:plan]" in prompt:
            return {
                "erp_impacts": [],
                "attention_points": [],
                "tests": [
                    {
                        "id": "CT01",
                        "title": "Validar desconto",
                        "priority": "P0",
                        "provenance": "story",
                        "category": "requirement",
                        "related_risks": [],
                    }
                ],
                "negative_tests": [],
                "regression": [],
                "questions": [],
            }
        raise AssertionError("unexpected stage")


class FakeLoader:
    def __init__(self, root):
        pass

    def load(self):
        return KnowledgeBase(
            version=2,
            modules=[
                KnowledgeModule(
                    name="Financeiro",
                    aliases=["financeiro"],
                    features=[
                        KnowledgeFeature(
                            name="Conta a Pagar",
                            aliases=["contas a pagar"],
                            keywords=["desconto"],
                        )
                    ],
                )
            ],
        )


def _patch(monkeypatch):
    FakeJiraClient.calls = 0
    FakeProvider.calls = 0
    monkeypatch.setattr(cli, "Settings", lambda: FakeSettings())
    monkeypatch.setattr(cli, "JiraClient", FakeJiraClient)
    monkeypatch.setattr(cli, "ClaudeCliProvider", FakeProvider)
    monkeypatch.setattr(cli, "KnowledgeLoader", FakeLoader)


def test_analysis_cli_saves_outputs_shows_progress_and_uses_cache(tmp_path: Path, monkeypatch):
    _patch(monkeypatch)
    monkeypatch.chdir(tmp_path)

    first = runner.invoke(cli.app, ["FN-14"])
    assert first.exit_code == 0, first.stdout
    issue_dir = tmp_path / ".qa" / "FN-14"
    assert (issue_dir / "story.json").exists()
    assert (issue_dir / "analysis.json").exists()
    assert (issue_dir / "analise-FN-14.md").exists()
    assert FakeProvider.calls == 2
    assert FakeJiraClient.calls == 1
    assert "Story carregada do Jira" in first.stdout
    assert "Interpretando requisito" in first.stdout
    assert "Analisando impacto e planejando testes" in first.stdout
    assert "Concluído em" in first.stdout

    second = runner.invoke(cli.app, ["FN-14"])
    assert second.exit_code == 0, second.stdout
    assert FakeProvider.calls == 2
    assert FakeJiraClient.calls == 1
    assert "cache" in second.stdout.lower()

    third = runner.invoke(cli.app, ["FN-14", "--reanalyze"])
    assert third.exit_code == 0, third.stdout
    assert FakeProvider.calls == 4
    assert FakeJiraClient.calls == 2
