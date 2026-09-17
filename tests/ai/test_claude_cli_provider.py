import json
import subprocess

import pytest

from qanalisa.ai.claude_cli_provider import ClaudeCliProvider
from qanalisa.ai.provider import AIProviderError

SCHEMA = {
    "type": "object",
    "properties": {"context": {"type": "string"}},
    "required": ["context"],
}


def test_build_command_uses_noninteractive_structured_safe_mode():
    provider = ClaudeCliProvider(command="claude", model="sonnet", timeout_seconds=120)
    cmd = provider.build_command(SCHEMA)

    assert cmd[:2] == ["claude", "-p"]
    assert "--output-format" in cmd and "json" in cmd
    assert "--json-schema" in cmd
    assert "--safe-mode" in cmd
    tools_index = cmd.index("--tools")
    assert cmd[tools_index + 1] == ""
    assert "--no-session-persistence" in cmd
    assert "--model" in cmd and "sonnet" in cmd


def test_generate_returns_structured_output(monkeypatch):
    provider = ClaudeCliProvider(command="claude", model=None, timeout_seconds=120)

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "structured_output": {"context": "ok"},
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert provider.generate("prompt", SCHEMA) == {"context": "ok"}


def test_generate_passes_prompt_through_stdin(monkeypatch):
    provider = ClaudeCliProvider(command="claude", model=None, timeout_seconds=120)
    captured = {}

    def fake_run(*args, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps({"structured_output": {"context": "ok"}}),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    provider.generate("conteúdo sensível da story", SCHEMA)
    assert captured["input"] == "conteúdo sensível da story"
    assert "conteúdo sensível da story" not in captured.get("args", [])


def test_preflight_warns_when_anthropic_api_key_is_present(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
    provider = ClaudeCliProvider(command="claude", model=None, timeout_seconds=120)
    warnings = provider.preflight()
    assert any("API billing" in warning for warning in warnings)
    assert all("secret" not in warning for warning in warnings)


@pytest.mark.parametrize(
    "failure",
    [
        FileNotFoundError(),
        subprocess.TimeoutExpired(cmd="claude", timeout=120),
    ],
)
def test_generate_wraps_process_failures(monkeypatch, failure):
    provider = ClaudeCliProvider(command="claude", model=None, timeout_seconds=120)

    def fake_run(*args, **kwargs):
        raise failure

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(AIProviderError):
        provider.generate("prompt", SCHEMA)


def test_generate_rejects_nonzero_exit(monkeypatch):
    provider = ClaudeCliProvider(command="claude", model=None, timeout_seconds=120)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 1, stdout="", stderr="auth failed"),
    )
    with pytest.raises(AIProviderError, match="Claude Code"):
        provider.generate("prompt", SCHEMA)


def test_generate_rejects_malformed_json(monkeypatch):
    provider = ClaudeCliProvider(command="claude", model=None, timeout_seconds=120)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, stdout="not-json", stderr=""),
    )
    with pytest.raises(AIProviderError, match="JSON"):
        provider.generate("prompt", SCHEMA)


def test_generate_requires_structured_output(monkeypatch):
    provider = ClaudeCliProvider(command="claude", model=None, timeout_seconds=120)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(
            a[0], 0, stdout=json.dumps({"result": "text only"}), stderr=""
        ),
    )
    with pytest.raises(AIProviderError, match="structured_output"):
        provider.generate("prompt", SCHEMA)
