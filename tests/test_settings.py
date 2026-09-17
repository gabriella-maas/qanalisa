from qanalisa.config.settings import Settings


def test_settings_reads_jira_and_claude_defaults(monkeypatch):
    monkeypatch.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "qa@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "secret")
    settings = Settings()
    assert settings.jira_base_url == "https://example.atlassian.net"
    assert settings.ai_provider == "claude_cli"
    assert settings.claude_command == "claude"
    assert settings.claude_timeout_seconds == 120
