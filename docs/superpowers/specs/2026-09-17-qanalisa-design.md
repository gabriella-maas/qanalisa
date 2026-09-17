# QAnalisa — Design Specification

**Date:** 2026-09-17  
**Status:** Approved; revised to Claude Code provider on 2026-09-17  
**Primary user:** QA analyst working with Jira Cloud and VRSuper ERP
**Product name:** QAnalisa
**Primary command:** `qanalisa`

## 1. Purpose

Build QAnalisa, a local modular CLI that reduces repetitive QA analysis work. Given a Jira issue key, the tool retrieves the issue key, title, and description, analyzes the requirement with an LLM, correlates it with a local VRSuper ERP knowledge base, and generates a structured QA analysis with prioritized test scenarios, regression suggestions, risks, and requirement gaps.

The MVP is intentionally read-only with respect to Jira. It will not create or edit Jira issues or comments.

## 2. Core User Experience

Primary command:

```bash
qanalisa FN-1234
```

The tool should:

1. Read the Jira issue key, title, and description.
2. Persist the raw issue snapshot locally.
3. Identify the primary VRSuper module and feature.
4. Extract explicit business rules and requested changes.
5. Match the task against the local VRSuper knowledge base.
6. Analyze possible ERP impacts and regression risks.
7. Generate prioritized, compact test scenarios.
8. Generate negative and boundary scenarios.
9. Generate a suggested regression checklist.
10. Identify ambiguities, missing acceptance criteria, and questions for PO/DEV.
11. Display the result in the terminal.
12. Save the result as structured JSON and Markdown.

### 2.1 Scenario expansion

```bash
qanalisa FN-1234 --test CT07
```

Expands a compact scenario into a full test case containing:

- title;
- priority;
- objective;
- preconditions;
- steps;
- expected result;
- related risk or business rule.

### 2.2 Reanalysis

```bash
qanalisa FN-1234 --reanalyze
```

Forces a new AI analysis using the locally saved story snapshot unless the implementation later adds an explicit Jira refresh option. Normal repeated execution should reuse cached analysis when possible.

### 2.3 Bug report generation

Short Jira-comment style:

```bash
qanalisa bug FN-1234
```

Full bug report:

```bash
qanalisa bug FN-1234 --full
```

The bug generator reuses the saved issue context and analysis so the user can describe the defect naturally without re-explaining the whole story.

Short output should be concise and ready to paste into Jira.

Full output should contain:

- title;
- preconditions;
- reproduction steps;
- actual result;
- expected result;
- evidence placeholder;
- impact.

### 2.4 Knowledge base commands

```bash
qanalisa knowledge update
qanalisa knowledge show Financeiro
qanalisa knowledge add
```

`knowledge update` refreshes documented knowledge from the official VRSuper documentation while preserving manually curated knowledge.

## 3. MVP Scope

### Included

- Python CLI for Linux.
- Jira Cloud read-only integration.
- Jira issue key, title, and description only.
- Claude Code-based analysis through a provider abstraction, using the locally authenticated corporate Claude subscription when available.
- Local structured workspace per Jira issue.
- Local VRSuper knowledge base.
- Hybrid VRSuper knowledge updates from official documentation.
- Manual knowledge additions.
- Compact prioritized scenarios plus on-demand expansion.
- ERP impact and regression analysis.
- Short and full bug report generation.
- Markdown and JSON outputs.
- Caching and reanalysis.
- Automated tests for deterministic parts of the tool.

### Explicitly out of scope for MVP

- Pull request, commit, branch, or code diff analysis.
- GitHub integration.
- Automatic Jira comments or Jira mutations.
- Jira attachments, subtasks, related issues, or comments.
- Browser UI.
- Team collaboration or shared server.
- Automatic test execution.
- Direct database access to the ERP.

These are future extensions and should not shape the MVP beyond preserving modular boundaries.

### 3.1 AI provider decision for the MVP

The MVP uses **Claude Code via the local `claude` CLI**, authenticated with the user's company Claude subscription when that organization/seat permits Claude Code. QAnalisa invokes Claude only as a non-interactive analysis engine; it does not delegate Jira access, filesystem discovery, or knowledge crawling to Claude.

The intended invocation pattern is `claude -p` with structured JSON output, a JSON Schema, bare mode, and no session persistence. This keeps QAnalisa responsible for context assembly and validation while Claude is responsible for language/reasoning stages.

Direct Anthropic API and OpenAI API integrations remain future provider implementations behind the same `AIProvider` interface; they are not required for the MVP.

## 4. Architecture

Recommended architecture: modular local CLI.

```text
                 qanalisa FN-1234
                      |
                +-----v-----+
                |    CLI    |
                +-----+-----+
                      |
       +--------------+--------------+
       |              |              |
       v              v              v
   Jira Client    Knowledge       Storage
                      |
                VRSuper Matrix
                      |
                      v
                 AI Analyzer
                      |
          +-----------+-----------+
          v           v           v
       context     scenarios    regression
                      |
                      v
                Report Builder
                 |          |
              terminal     .md
```

### 4.1 Proposed package layout

```text
qanalisa/
├── src/
│   └── qanalisa/
│       ├── cli.py
│       ├── config/
│       │   └── settings.py
│       ├── jira/
│       │   ├── client.py
│       │   └── parser.py
│       ├── knowledge/
│       │   ├── loader.py
│       │   ├── updater.py
│       │   └── matcher.py
│       ├── ai/
│       │   ├── provider.py
│       │   └── claude_cli_provider.py
│       ├── analysis/
│       │   ├── story_analyzer.py
│       │   ├── impact_analyzer.py
│       │   ├── test_generator.py
│       │   └── bug_generator.py
│       ├── storage/
│       │   └── workspace.py
│       └── reports/
│           └── markdown.py
├── knowledge/
│   └── vrsuper/
│       ├── modules.yaml
│       ├── relationships.yaml
│       ├── risks.yaml
│       ├── manual.yaml
│       ├── sources.yaml
│       └── metadata.json
├── tests/
├── .env.example
├── .gitignore
└── pyproject.toml
```

## 5. Component Responsibilities

### CLI

Owns command parsing and user interaction only. It should coordinate services but not contain Jira, AI, or knowledge logic.

### Jira client

Owns Jira HTTP calls and authentication. The MVP is read-only.

### Jira parser

Converts Jira's raw response into an internal issue model with at least:

```json
{
  "key": "FN-1234",
  "title": "...",
  "description": "..."
}
```

### Knowledge loader

Loads versioned local YAML/JSON knowledge.

### Knowledge matcher

Finds likely module, feature, relationships, and known risks relevant to the story. It must return confidence/provenance rather than silently asserting weak matches.

### Knowledge updater

Reads official VRSuper documentation, identifies documented modules/features/relationships, compares them to the local base, and updates only documented knowledge. It must preserve manual knowledge.

### AI provider abstraction

Defines an interface independent of any model provider. The MVP implementation is `ClaudeCliProvider`, which invokes Claude Code non-interactively through `claude -p`. Future providers such as OpenAI API, Anthropic API, or local models must be replaceable without changing the core analysis pipeline.

### Claude CLI provider

`ClaudeCliProvider` is the default MVP provider. It should:

- invoke Claude Code with `claude -p` in non-interactive mode;
- request machine-readable output with `--output-format json`;
- use `--json-schema` whenever the analysis stage has a known schema;
- use `--safe-mode` so local Claude skills/plugins/MCP/CLAUDE.md do not contaminate deterministic QAnalisa analysis;
- use `--no-session-persistence` for one-shot QAnalisa analyses;
- enforce a subprocess timeout;
- treat non-zero exit codes, malformed output, auth failures, and usage-limit errors as provider failures;
- never expose authentication tokens, environment secrets, or full subprocess environments in logs;
- be unit-tested through mocked subprocess calls rather than live Claude usage.

The provider receives all task and VRSuper context explicitly from QAnalisa. Claude must not need filesystem, browser, shell, Jira, or network tools to perform the analysis itself.

### Story analyzer

Extracts explicit story facts:

- requested changes;
- explicit business rules;
- feature/module candidates;
- entities;
- conditions;
- exceptions;
- requirement gaps.

### Impact analyzer

Combines story facts with VRSuper knowledge to identify potential ERP impacts and regression areas.

### Test generator

Creates prioritized compact test scenarios from explicit requirements plus impact analysis.

### Bug generator

Combines issue context, previous analysis, and the user's defect description to produce concise or full bug reports.

### Workspace storage

Persists source issue snapshot, structured analysis, reports, and bug reports.

### Markdown report builder

Transforms structured analysis into human-readable Markdown. Presentation should not be the source of truth; structured JSON is the canonical generated analysis.

## 6. Data Flow

### 6.1 Story analysis flow

```text
Jira issue
   |
   v
Raw snapshot
   |
   v
Structured requirement extraction
   |
   +----> VRSuper knowledge match
   |              |
   +--------------+
          |
          v
ERP impact analysis
          |
          v
Test generation
          |
          v
Structured analysis.json
          |
          +----> terminal
          +----> Markdown report
```

The tool should avoid a single monolithic "analyze everything" prompt. Analysis should be separated into structured stages so facts from the story are not mixed with model hypotheses.

## 7. Fact, Inference, and Provenance Model

Every important conclusion should be attributable to one of these categories:

- `story`: explicitly present in the Jira title or description.
- `documented`: supported by official VRSuper documentation.
- `manual`: curated internal QA knowledge stored locally.
- `inferred`: AI/ERP reasoning not directly documented.
- `unknown`: requires confirmation.

Human-readable reports should distinguish them, for example:

```text
✓ Identified in the story
✓ Documented VRSuper relationship
★ Manually curated QA knowledge
≈ Inferred potential impact
? Requires confirmation
```

A potential impact must never be rendered as a confirmed dependency unless supported by documented or manual knowledge.

## 8. VRSuper Knowledge Model

The local knowledge base should encode more than module names. Each relationship may include:

- source module;
- feature/submodule;
- related module/feature;
- reason for relationship;
- risks;
- source URL/reference;
- source type;
- confidence;
- last updated metadata.

Example:

```yaml
modules:
  Financeiro:
    features:
      ContaAPagar:
        related_modules:
          - module: Fiscal
            reason: "Títulos podem ser originados por recebimento de nota fiscal"
            confidence: documented
            source_type: documented
            source: "https://docs.vrsoft.com.br/..."
            risks:
              - "divergência entre valor fiscal e financeiro"
              - "título não gerado após recebimento"
              - "cancelamento sem reflexo financeiro"
```

### 8.1 Knowledge update behavior

`qanalisa knowledge update` should:

1. Read the official VRSuper documentation.
2. Discover documented modules, submodules, features, and cross-references.
3. Compare discovered data with the local documented knowledge.
4. Produce a readable diff.
5. Update documented knowledge.
6. Preserve all manual knowledge.
7. Update metadata, including source and update time.

It must not silently delete manual knowledge.

### 8.2 Manual knowledge

Manual knowledge exists because production/testing behavior may be more useful than documentation alone. Manual entries should be explicitly marked so future documentation updates do not overwrite them.

## 9. Analysis Output Model

`analysis.json` should contain at least:

```json
{
  "issue": "FN-1234",
  "generated_at": "...",
  "model": "...",
  "knowledge_version": 1,
  "module": {
    "name": "Financeiro",
    "confidence": 0.95
  },
  "feature": "Conta a Pagar",
  "context": "...",
  "changes": [],
  "business_rules": [],
  "scope": [],
  "attention_points": [],
  "erp_impacts": [],
  "tests": [],
  "negative_tests": [],
  "regression": [],
  "questions": []
}
```

Exact schema can be refined during implementation, but the structured output must remain stable enough to power Markdown, scenario expansion, and future UI/API layers.

## 10. Human-Readable Report Structure

```text
# FN-1234 — Title

## 1. Contexto da tarefa
## 2. O que está sendo alterado
## 3. Regras de negócio identificadas
## 4. Escopo da tarefa
## 5. Pontos de atenção
## 6. Impacto no ERP VRSuper
### Módulo principal
### Módulos relacionados
### Possíveis efeitos colaterais
## 7. Cenários de teste
## 8. Cenários negativos e de borda
## 9. Regressivo sugerido
## 10. Dúvidas / lacunas do requisito
```

Compact scenarios should look like:

```text
[P0] CT01 — Inativar contrato válido
[P0] CT02 — Consultar contrato após inativação
[P1] CT03 — Inativar contrato já inativo
[P1] CT04 — Consultar por período após inativação
```

Priority semantics:

- `P0`: core business flow / high-risk regression / must-test.
- `P1`: important variation or meaningful negative/related flow.
- `P2`: lower-risk edge or optional regression check.

The exact prioritization rubric should be encoded in prompts and documented in code/tests.

## 11. Local Workspace

Per issue:

```text
.qa/
└── FN-1234/
    ├── story.json
    ├── analysis.json
    ├── analise-FN-1234.md
    └── bugs/
```

`story.json` should preserve the Jira snapshot used for the analysis. This enables reproducibility and reanalysis without automatically refetching Jira.

## 12. Configuration and Secrets

Local `.env`:

```text
JIRA_BASE_URL=https://company.atlassian.net
JIRA_EMAIL=
JIRA_API_TOKEN=
AI_PROVIDER=claude_cli
CLAUDE_COMMAND=claude
CLAUDE_MODEL=
CLAUDE_TIMEOUT_SECONDS=120
```

`.env` must be ignored by Git.

`.env.example` must contain placeholders only.


Claude Code authentication is performed separately through the installed `claude` CLI using the company Claude account. QAnalisa must not ask the user to paste Claude OAuth credentials or session tokens.

If the machine has an `ANTHROPIC_API_KEY` environment variable set, Claude Code may authenticate through API billing instead of the subscription. QAnalisa should detect this condition during provider preflight and warn the user before analysis, because the intended MVP path is subscription-authenticated Claude Code.

Security rules:

- Jira token should be read-only/scoped for MVP.
- Never log API tokens, API keys, or authorization headers.
- Error messages must not dump sensitive request headers.
- Secrets must never be written into issue workspaces or generated reports.

## 13. Cost and Cache Behavior

Claude usage follows the limits and billing rules of the authenticated company Claude plan. The MVP should still avoid unnecessary repeat calls and respect organization usage limits.

Default behavior:

```text
qanalisa FN-1234
```

If a compatible cached analysis exists, reuse it and tell the user when it was generated.

```text
qanalisa FN-1234 --reanalyze
```

Forces a new AI analysis.

Generated analysis should record:

- generation timestamp;
- model name;
- knowledge version;
- optionally prompt/schema version for reproducibility.

## 14. Error Handling

### Jira issue not found or inaccessible

Provide a clear message and no stack trace by default.

### Jira succeeds, AI fails

Persist the story snapshot and tell the user they can re-run analysis later.

### No VRSuper knowledge match

Continue with story + general ERP reasoning, but explicitly lower confidence for knowledge-based regression suggestions.

### Invalid AI response

Validate structured AI output against a schema and retry or fail cleanly rather than generating a malformed report.

### Knowledge update failure

Keep the existing knowledge base intact. Updates should be written atomically so a failed refresh cannot corrupt the current local base.

## 15. Testing Strategy

Prioritize deterministic tests.

### Jira parser

- extracts title;
- extracts description;
- handles empty description;
- handles Jira rich-text structures.

### Knowledge matcher

- matches known modules/features;
- returns relationships with provenance;
- handles no-match cases;
- never fabricates a stored relationship.

### Workspace

- saves story snapshot;
- loads cached analysis;
- preserves bug history;
- handles reanalysis safely.

### CLI

- parses `qanalisa FN-1234`;
- parses `--reanalyze`;
- parses `--test CT04`;
- parses `qanalisa bug FN-1234`;
- parses `qanalisa bug FN-1234 --full`;
- parses knowledge commands.

### Claude CLI provider

- builds the expected non-interactive command;
- parses successful JSON output;
- extracts `structured_output` when `--json-schema` is used;
- reports missing `claude` executable clearly;
- reports timeout cleanly;
- handles non-zero exit codes without leaking stderr secrets;
- warns when `ANTHROPIC_API_KEY` is present;
- never performs a live Claude call in the normal test suite.

### AI contracts

Do not assert exact prose. Validate required structured fields and allowed enum/provenance values.

Use mocked provider responses in normal automated tests to avoid network dependency and API cost.

## 16. MVP Acceptance Criteria

The MVP is usable when all of the following work end-to-end:

### `qanalisa FN-1234`

- authenticates to Jira Cloud;
- reads key, title, and description;
- saves the story snapshot;
- identifies likely module/feature;
- extracts explicit changes and business rules;
- correlates with local VRSuper knowledge;
- generates prioritized scenarios;
- generates negative/boundary scenarios;
- generates ERP impact and regression suggestions;
- identifies requirement gaps/questions;
- prints a useful terminal result;
- writes `analysis.json` and Markdown.

### `qanalisa FN-1234 --test CT03`

- expands the requested stored scenario into a detailed test case.

### `qanalisa bug FN-1234`

- accepts a natural-language defect description;
- reuses saved issue context;
- outputs a concise Jira-ready comment.

### `qanalisa bug FN-1234 --full`

- outputs a complete structured bug report.

### `qanalisa knowledge update`

- refreshes documented VRSuper knowledge;
- shows a diff/summary;
- preserves manual knowledge;
- does not corrupt the current base on failure.

## 17. Future Extensions

Not part of MVP, but the architecture should permit later addition of:

- Jira comments, attachments, linked issues, and subtasks;
- GitHub PR, commit, and diff analysis;
- screenshot/error-log analysis for bug reports;
- browser UI;
- shared/team knowledge service;
- test execution tracking;
- Jira comment publishing with explicit confirmation;
- additional LLM providers such as OpenAI API, direct Anthropic API, or local models.

## 18. Key Design Principles

1. **Read-only first.** The MVP must not mutate Jira.
2. **Facts before inference.** Story facts and documented ERP relations are distinct from model hypotheses.
3. **Structured data first.** JSON is canonical; Markdown is presentation.
4. **Local and inspectable.** The user can see and version the knowledge base and per-task workspace.
5. **Provider-independent AI boundary.** Claude Code is the first provider, not a hard-coded architectural dependency.
6. **Incremental knowledge.** Official documentation and manual QA knowledge coexist without overwriting each other.
7. **Small MVP.** No PR analysis, UI, Jira writeback, or automatic execution in the first version.


## Claude Code isolation note

The MVP invokes Claude Code in non-interactive `-p` mode with `--safe-mode`, `--tools ""`, and `--no-session-persistence` so it keeps subscription authentication while disabling local project instructions, plugins, MCPs, skills, hooks, and tool execution.
