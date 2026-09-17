# QAnalisa Core Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working `qanalisa FN-1234` flow: read a Jira card, analyze it with subscription-authenticated Claude Code, correlate it with local VRSuper knowledge, print the analysis, and save JSON/Markdown with cache support.

**Architecture:** Python 3.12 package using Typer for CLI, httpx for Jira, Pydantic for typed models, PyYAML for local knowledge, Rich for terminal output, and a provider boundary around a subprocess-based Claude Code integration. Claude receives task and knowledge context explicitly through `claude -p`; the provider uses structured output and does not grant Claude filesystem or Jira access.

**Tech Stack:** Python 3.12+, Typer, Pydantic 2, pydantic-settings, httpx, PyYAML, Rich, pytest, pytest-mock.

**Spec:** `docs/superpowers/specs/2026-09-17-qanalisa-design.md`

## Global Constraints

- Linux-first local CLI.
- Jira is read-only in MVP.
- Read only Jira key, title, and description.
- Claude Code is the default AI provider and is authenticated separately through the company Claude subscription.
- Do not store or request Claude OAuth/session credentials.
- Warn before analysis when `ANTHROPIC_API_KEY` is present because it may route Claude Code through API billing.
- Never print Jira tokens, API keys, authorization headers, or complete process environments.
- JSON is canonical output; Markdown and terminal output are projections.
- Story facts, documented knowledge, manual knowledge, inference, and unknowns remain distinguishable.
- Unit tests must mock Jira and Claude; normal tests must not require network access or consume Claude usage.
- Repeated `qanalisa FN-1234` uses cache unless `--reanalyze` is supplied.

---

## File Map

- `pyproject.toml` — packaging, dependencies, `qanalisa` console entry point, pytest configuration.
- `.gitignore` — secrets, virtualenv, caches, generated `.qa` workspaces.
- `.env.example` — non-secret Jira and Claude CLI configuration placeholders.
- `src/qanalisa/cli.py` — Typer commands and orchestration only.
- `src/qanalisa/config/settings.py` — environment-backed settings and safe validation.
- `src/qanalisa/models.py` — shared Pydantic models for Jira issue, provenance, analysis, tests, and metadata.
- `src/qanalisa/jira/client.py` — read-only Jira HTTP client.
- `src/qanalisa/jira/parser.py` — Jira ADF/plain-text description normalization.
- `src/qanalisa/ai/provider.py` — provider protocol and provider errors.
- `src/qanalisa/ai/claude_cli_provider.py` — `claude -p` subprocess adapter.
- `src/qanalisa/knowledge/loader.py` — load versioned local VRSuper YAML/JSON.
- `src/qanalisa/knowledge/matcher.py` — match story terms to modules/features and return provenance.
- `src/qanalisa/storage/workspace.py` — issue workspace persistence and cache decisions.
- `src/qanalisa/analysis/story_analyzer.py` — structured extraction of explicit story facts.
- `src/qanalisa/analysis/impact_analyzer.py` — combine story facts and VRSuper relationships.
- `src/qanalisa/analysis/test_generator.py` — compact prioritized test scenarios/regression/questions.
- `src/qanalisa/analysis/pipeline.py` — orchestrate analysis stages.
- `src/qanalisa/reports/markdown.py` — deterministic Markdown projection.
- `knowledge/vrsuper/*.yaml|json` — seed VRSuper knowledge and metadata.
- `tests/` — unit/integration tests with local fixtures and mocks.

---

### Task 1: Package bootstrap, settings, and CLI shell

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/qanalisa/__init__.py`
- Create: `src/qanalisa/cli.py`
- Create: `src/qanalisa/config/__init__.py`
- Create: `src/qanalisa/config/settings.py`
- Test: `tests/test_settings.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces: `Settings.load() -> Settings`
- Produces: Typer application `app`
- Produces console command: `qanalisa`

- [ ] **Step 1: Write failing settings tests**

```python
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
```

- [ ] **Step 2: Run the settings test and confirm it fails**

Run: `pytest tests/test_settings.py -q`
Expected: import/module failure because settings do not exist yet.

- [ ] **Step 3: Create package metadata and settings**

Use this dependency set in `pyproject.toml`:

```toml
[project]
name = "qanalisa"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "typer>=0.12,<1",
  "rich>=13,<15",
  "httpx>=0.27,<1",
  "pydantic>=2.8,<3",
  "pydantic-settings>=2.4,<3",
  "PyYAML>=6,<7",
]

[project.optional-dependencies]
dev = ["pytest>=8,<9", "pytest-mock>=3.14,<4"]

[project.scripts]
qanalisa = "qanalisa.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/qanalisa"]
```

Create `Settings` with `pydantic-settings`; use `env_file=".env"`, ignore unknown fields, and define `ai_provider="claude_cli"`, `claude_command="claude"`, optional `claude_model`, and `claude_timeout_seconds=120`.

- [ ] **Step 4: Add a CLI shell test**

```python
from typer.testing import CliRunner
from qanalisa.cli import app

runner = CliRunner()


def test_cli_help_mentions_qanalisa():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "QAnalisa" in result.stdout
```

- [ ] **Step 5: Implement minimal Typer app and run tests**

`src/qanalisa/cli.py` should define `app = typer.Typer(help="QAnalisa — Entenda a story. Mapeie o risco. Teste melhor.")` and a placeholder analysis command signature that will be filled in later.

Run: `pytest tests/test_settings.py tests/test_cli.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .gitignore .env.example src/qanalisa tests/test_settings.py tests/test_cli.py
git commit -m "chore: bootstrap qanalisa cli"
```

---

### Task 2: Jira issue model, ADF parser, and read-only client

**Files:**
- Create: `src/qanalisa/models.py`
- Create: `src/qanalisa/jira/__init__.py`
- Create: `src/qanalisa/jira/parser.py`
- Create: `src/qanalisa/jira/client.py`
- Test: `tests/jira/test_parser.py`
- Test: `tests/jira/test_client.py`

**Interfaces:**
- Produces: `JiraIssue(key: str, title: str, description: str)`
- Produces: `parse_description(value: object) -> str`
- Produces: `JiraClient.get_issue(issue_key: str) -> JiraIssue`

- [ ] **Step 1: Write parser tests for plain text, ADF, and empty description**

```python
from qanalisa.jira.parser import parse_description


def test_parse_adf_description():
    adf = {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Regra A"}]}],
    }
    assert parse_description(adf) == "Regra A"


def test_parse_empty_description():
    assert parse_description(None) == ""
```

- [ ] **Step 2: Run parser tests and confirm failure**

Run: `pytest tests/jira/test_parser.py -q`
Expected: FAIL because parser is missing.

- [ ] **Step 3: Implement recursive ADF text extraction**

The parser must collect `text` nodes, preserve paragraph/list boundaries with newlines, and return a normalized string with repeated blank lines collapsed.

- [ ] **Step 4: Write a mocked Jira client test**

```python
import httpx
from qanalisa.jira.client import JiraClient


def test_get_issue_requests_only_summary_and_description(monkeypatch):
    captured = {}

    def handler(request: httpx.Request):
        captured["url"] = str(request.url)
        return httpx.Response(200, json={
            "key": "FN-14",
            "fields": {"summary": "Teste", "description": None},
        })

    client = JiraClient(
        base_url="https://example.atlassian.net",
        email="qa@example.com",
        token="secret",
        transport=httpx.MockTransport(handler),
    )
    issue = client.get_issue("FN-14")
    assert issue.key == "FN-14"
    assert "fields=summary%2Cdescription" in captured["url"]
```

- [ ] **Step 5: Implement JiraClient with safe errors**

Use `GET /rest/api/3/issue/{issueKey}?fields=summary,description`, HTTP basic auth `(email, token)`, and map 401/403/404 into a `JiraError` message that contains the issue key and status but never the token or authorization header.

- [ ] **Step 6: Run Jira tests**

Run: `pytest tests/jira -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/qanalisa/models.py src/qanalisa/jira tests/jira
git commit -m "feat: read jira card context"
```

---

### Task 3: Local workspace and cache behavior

**Files:**
- Create: `src/qanalisa/storage/__init__.py`
- Create: `src/qanalisa/storage/workspace.py`
- Test: `tests/storage/test_workspace.py`

**Interfaces:**
- Produces: `Workspace(root: Path)`
- Produces: `save_story(issue: JiraIssue) -> Path`
- Produces: `load_story(issue_key: str) -> JiraIssue | None`
- Produces: `save_analysis(issue_key: str, analysis: AnalysisResult) -> Path`
- Produces: `load_analysis(issue_key: str) -> AnalysisResult | None`

- [ ] **Step 1: Write persistence tests**

```python
from pathlib import Path
from qanalisa.models import JiraIssue
from qanalisa.storage.workspace import Workspace


def test_story_roundtrip(tmp_path: Path):
    ws = Workspace(tmp_path / ".qa")
    issue = JiraIssue(key="FN-14", title="Teste", description="Descrição")
    ws.save_story(issue)
    assert ws.load_story("FN-14") == issue
```

- [ ] **Step 2: Run test and confirm failure**

Run: `pytest tests/storage/test_workspace.py -q`
Expected: FAIL because workspace does not exist.

- [ ] **Step 3: Implement atomic JSON persistence**

Write to a sibling temporary file and `Path.replace()` it into place. Store under `.qa/<ISSUE>/story.json` and `.qa/<ISSUE>/analysis.json`.

- [ ] **Step 4: Add cache metadata test**

Test that `generated_at`, `provider`, `model`, `knowledge_version`, and `schema_version` survive roundtrip on `AnalysisResult`.

- [ ] **Step 5: Run storage tests and commit**

Run: `pytest tests/storage -q`
Expected: PASS.

```bash
git add src/qanalisa/storage tests/storage src/qanalisa/models.py
git commit -m "feat: add local issue workspace"
```

---

### Task 4: Claude Code provider with structured output

**Files:**
- Create: `src/qanalisa/ai/__init__.py`
- Create: `src/qanalisa/ai/provider.py`
- Create: `src/qanalisa/ai/claude_cli_provider.py`
- Test: `tests/ai/test_claude_cli_provider.py`

**Interfaces:**
- Produces protocol: `AIProvider.generate(prompt: str, schema: dict) -> dict`
- Produces: `ClaudeCliProvider(command: str, model: str | None, timeout_seconds: int)`
- Produces: `ClaudeCliProvider.preflight() -> list[str]` warnings

- [ ] **Step 1: Write command-building test**

```python
from qanalisa.ai.claude_cli_provider import ClaudeCliProvider


def test_build_command_uses_noninteractive_structured_safe_mode():
    provider = ClaudeCliProvider(command="claude", model="sonnet", timeout_seconds=120)
    cmd = provider.build_command({"type": "object", "properties": {"context": {"type": "string"}}, "required": ["context"]})
    assert cmd[:2] == ["claude", "-p"]
    assert "--output-format" in cmd and "json" in cmd
    assert "--json-schema" in cmd
    assert "--safe-mode" in cmd
    assert "--tools" in cmd and "" in cmd
    assert "--no-session-persistence" in cmd
    assert "--model" in cmd and "sonnet" in cmd
```

- [ ] **Step 2: Run provider tests and confirm failure**

Run: `pytest tests/ai/test_claude_cli_provider.py -q`
Expected: FAIL because provider is missing.

- [ ] **Step 3: Implement provider command construction**

The final command shape must be equivalent to:

```bash
claude -p \
  --output-format json \
  --json-schema '<schema-json>' \
  --safe-mode \
  --tools "" \
  --no-session-persistence \
  --model sonnet
```

Pass the prompt to `subprocess.run(..., input=prompt, text=True, capture_output=True, timeout=...)` rather than placing the full Jira story in the process argument list.

- [ ] **Step 4: Write successful JSON parsing test**

Mock `subprocess.run` to return:

```json
{"type":"result","subtype":"success","is_error":false,"structured_output":{"context":"ok"}}
```

Assert `generate()` returns `{"context": "ok"}`.

- [ ] **Step 5: Add failure/preflight tests**

Cover missing executable, timeout, non-zero exit code, malformed JSON, missing `structured_output`, and `ANTHROPIC_API_KEY` present. The API-key condition must return a warning such as `ANTHROPIC_API_KEY is set; Claude Code may use API billing instead of the subscription.`

- [ ] **Step 6: Implement safe error handling and run tests**

Run: `pytest tests/ai -q`
Expected: PASS with no live Claude call.

- [ ] **Step 7: Commit**

```bash
git add src/qanalisa/ai tests/ai
git commit -m "feat: add claude code provider"
```

---

### Task 5: Seed VRSuper knowledge loader and matcher

**Files:**
- Create: `knowledge/vrsuper/modules.yaml`
- Create: `knowledge/vrsuper/relationships.yaml`
- Create: `knowledge/vrsuper/risks.yaml`
- Create: `knowledge/vrsuper/manual.yaml`
- Create: `knowledge/vrsuper/sources.yaml`
- Create: `knowledge/vrsuper/metadata.json`
- Create: `src/qanalisa/knowledge/__init__.py`
- Create: `src/qanalisa/knowledge/loader.py`
- Create: `src/qanalisa/knowledge/matcher.py`
- Test: `tests/knowledge/test_loader.py`
- Test: `tests/knowledge/test_matcher.py`

**Interfaces:**
- Produces: `KnowledgeBase`
- Produces: `KnowledgeLoader.load() -> KnowledgeBase`
- Produces: `KnowledgeMatcher.match(text: str) -> KnowledgeMatch`

- [ ] **Step 1: Write loader test using a temporary fixture directory**

Assert version metadata and a documented `Financeiro > Conta a Pagar` feature load with source type preserved.

- [ ] **Step 2: Run loader test and confirm failure**

Run: `pytest tests/knowledge/test_loader.py -q`
Expected: FAIL.

- [ ] **Step 3: Implement typed knowledge models and loader**

Reject invalid provenance values; allowed values are `story`, `documented`, `manual`, `inferred`, `unknown` where applicable.

- [ ] **Step 4: Write matcher tests**

Use text containing `contas a pagar`, `título`, and `desconto` and assert Financeiro/Conta a Pagar is returned. Add a no-match test that returns an empty/low-confidence match rather than fabricating a relationship.

- [ ] **Step 5: Implement deterministic keyword-first matcher**

For MVP, normalize accents/case, score module and feature aliases from the YAML, and return related documented/manual risks. Do not ask Claude to invent the stored relationship graph.

- [ ] **Step 6: Seed a minimal documented knowledge set**

Seed only relationships already verified from official VRSuper docs, each with source URL and `source_type: documented`. Keep this seed intentionally small; Plan 3 expands it through `knowledge update`.

- [ ] **Step 7: Run tests and commit**

Run: `pytest tests/knowledge -q`
Expected: PASS.

```bash
git add knowledge/vrsuper src/qanalisa/knowledge tests/knowledge
git commit -m "feat: add vrsuper knowledge matching"
```

---

### Task 6: Structured story analysis, impact analysis, and test generation

**Files:**
- Create: `src/qanalisa/analysis/__init__.py`
- Create: `src/qanalisa/analysis/story_analyzer.py`
- Create: `src/qanalisa/analysis/impact_analyzer.py`
- Create: `src/qanalisa/analysis/test_generator.py`
- Create: `src/qanalisa/analysis/pipeline.py`
- Modify: `src/qanalisa/models.py`
- Test: `tests/analysis/test_story_analyzer.py`
- Test: `tests/analysis/test_pipeline.py`

**Interfaces:**
- Produces: `StoryFacts`
- Produces: `ImpactAnalysis`
- Produces: `AnalysisResult`
- Produces: `AnalysisPipeline.analyze(issue: JiraIssue, knowledge: KnowledgeMatch) -> AnalysisResult`

- [ ] **Step 1: Define Pydantic output models and JSON Schemas**

`StoryFacts` must include `context`, `changes`, `business_rules`, `scope`, `attention_points`, `module_candidates`, `feature_candidates`, and `questions`, with provenance on factual claims.

`AnalysisResult` must include the spec fields plus metadata, compact tests, negative tests, ERP impacts, and regression items.

- [ ] **Step 2: Write analyzer test with a fake provider**

```python
class FakeProvider:
    def generate(self, prompt: str, schema: dict) -> dict:
        return {
            "context": "Registrar desconto de contrato em acordo comercial",
            "changes": [{"text": "Mapear desconto", "provenance": "story"}],
            "business_rules": [],
            "scope": [],
            "attention_points": [],
            "module_candidates": ["Financeiro"],
            "feature_candidates": ["Conta a Pagar"],
            "questions": [],
        }
```

Assert `StoryAnalyzer` validates and returns `StoryFacts`.

- [ ] **Step 3: Implement prompts that explicitly separate facts from hypotheses**

Prompts must say that content absent from the story cannot be labeled `story`; uncertain behavior must be `unknown` or `inferred`.

- [ ] **Step 4: Implement impact/test stages using explicit knowledge context**

The prompt receives a compact serialized knowledge match including relationship reason and provenance. It must produce regression suggestions as potential checks, not confirmed impacts, unless supported by documented/manual knowledge.

- [ ] **Step 5: Write pipeline test asserting stage order and provenance preservation**

Use a fake provider with stage-specific returns. Assert documented knowledge remains `documented` and inferred regression stays `inferred`.

- [ ] **Step 6: Run analysis tests and commit**

Run: `pytest tests/analysis -q`
Expected: PASS.

```bash
git add src/qanalisa/analysis src/qanalisa/models.py tests/analysis
git commit -m "feat: generate structured qa analysis"
```

---

### Task 7: Markdown report, terminal rendering, cache/reanalyze, and end-to-end CLI

**Files:**
- Create: `src/qanalisa/reports/__init__.py`
- Create: `src/qanalisa/reports/markdown.py`
- Modify: `src/qanalisa/cli.py`
- Test: `tests/reports/test_markdown.py`
- Test: `tests/test_cli_analysis.py`

**Interfaces:**
- Produces: `render_markdown(issue: JiraIssue, analysis: AnalysisResult) -> str`
- CLI: `qanalisa ISSUE_KEY [--reanalyze]`

- [ ] **Step 1: Write Markdown snapshot-style assertions**

Check the rendered text contains the ten approved report sections and provenance markers `✓`, `★`, `≈`, `?` where corresponding data exists.

- [ ] **Step 2: Implement deterministic Markdown rendering**

Do not call Claude from the report layer. Render compact tests as `[P0] CT01 — ...`.

- [ ] **Step 3: Write CLI integration test with mocked Jira/provider/knowledge**

First invocation must save `.qa/FN-14/story.json`, `.qa/FN-14/analysis.json`, and `.qa/FN-14/analise-FN-14.md`. Second invocation without `--reanalyze` must not call the provider again. Invocation with `--reanalyze` must call the provider.

- [ ] **Step 4: Implement orchestration in CLI**

Flow: load settings → provider preflight warnings → cache check → fetch Jira when needed → save story → load/match knowledge → pipeline analyze → save analysis → render/save Markdown → print concise Rich summary and output path.

- [ ] **Step 5: Run the full core suite**

Run: `pytest -q`
Expected: PASS with zero network access and zero live Claude invocations.

- [ ] **Step 6: Manual preflight smoke test on Linux**

Run:

```bash
claude --version
qanalisa --help
```

Then, only after Claude is authenticated with the company subscription and Jira `.env` is configured:

```bash
qanalisa FN-14
```

Expected: Jira card is read, analysis appears, and `.qa/FN-14/` contains story/analysis/Markdown. If `ANTHROPIC_API_KEY` exists, QAnalisa warns before invoking Claude.

- [ ] **Step 7: Commit**

```bash
git add src/qanalisa/reports src/qanalisa/cli.py tests/reports tests/test_cli_analysis.py
git commit -m "feat: complete qanalisa core analysis flow"
```

---

## Core Plan Completion Check

Run:

```bash
pytest -q
qanalisa --help
```

The core plan is complete only when the automated suite passes and a configured Linux machine can run `qanalisa FN-14` end-to-end with Jira + Claude Code.
