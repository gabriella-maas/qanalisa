# QAnalisa Test Expansion and Bug Workflows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add on-demand test-case expansion plus short and full Jira-ready bug reports that reuse a saved QAnalisa issue workspace.

**Architecture:** Reuse the provider abstraction, structured models, and workspace from the core plan. Scenario expansion and bug generation each get their own schema and prompt, with deterministic CLI/persistence around mocked Claude calls.

**Tech Stack:** Existing QAnalisa Python stack; no new runtime dependency.

**Spec:** `docs/superpowers/specs/2026-09-17-qanalisa-design.md`

## Global Constraints

- Requires Core Analysis plan complete.
- Never re-fetch Jira merely to expand a stored test or generate a bug when the workspace already contains the required context.
- Bug text is generated for copy/paste only; QAnalisa does not write to Jira.
- Normal automated tests mock Claude Code.

---

### Task 1: Detailed scenario expansion

**Files:**
- Create: `src/qanalisa/analysis/scenario_expander.py`
- Modify: `src/qanalisa/models.py`
- Modify: `src/qanalisa/cli.py`
- Test: `tests/analysis/test_scenario_expander.py`
- Test: `tests/test_cli_scenario.py`

**Interfaces:**
- Produces: `DetailedTestCase`
- Produces: `ScenarioExpander.expand(issue, analysis, scenario_id) -> DetailedTestCase`
- CLI: `qanalisa FN-1234 --test CT07`

- [ ] **Step 1: Add a failing test for an existing scenario**

Use cached `AnalysisResult` containing `CT07`; fake provider returns title, priority, objective, preconditions, steps, expected result, and related risk.

- [ ] **Step 2: Add a failing test for an unknown scenario ID**

Expect a user-facing error `Scenario CT99 was not found in the cached analysis.` and no provider call.

- [ ] **Step 3: Implement `DetailedTestCase` and Claude schema**

Require non-empty `steps` and `expected_result`; preserve the original compact scenario priority.

- [ ] **Step 4: Implement CLI route and run tests**

Run: `pytest tests/analysis/test_scenario_expander.py tests/test_cli_scenario.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/qanalisa/analysis/scenario_expander.py src/qanalisa/models.py src/qanalisa/cli.py tests/analysis/test_scenario_expander.py tests/test_cli_scenario.py
git commit -m "feat: expand qanalisa test scenarios"
```

---

### Task 2: Short and full bug generation

**Files:**
- Create: `src/qanalisa/analysis/bug_generator.py`
- Modify: `src/qanalisa/models.py`
- Test: `tests/analysis/test_bug_generator.py`

**Interfaces:**
- Produces: `ShortBugReport(text: str)`
- Produces: `FullBugReport(title, preconditions, steps, actual_result, expected_result, evidence, impact)`
- Produces: `BugGenerator.generate_short(...)` and `generate_full(...)`

- [ ] **Step 1: Write short bug test**

Given user text `inativei o contrato, mostrou sucesso, depois consulta por período retornou 500`, assert the fake-provider result validates as a concise Jira-comment style report and does not invent reproduction details not present in context.

- [ ] **Step 2: Write full bug test**

Assert all full-report fields are present. Unknown preconditions/evidence must be expressed as `Não informado` or a question rather than fabricated facts.

- [ ] **Step 3: Implement prompts and schemas**

The prompt receives the saved Jira issue, relevant `analysis.json`, and the user's defect description. It must distinguish observed behavior from inferred expected behavior.

- [ ] **Step 4: Run tests**

Run: `pytest tests/analysis/test_bug_generator.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/qanalisa/analysis/bug_generator.py src/qanalisa/models.py tests/analysis/test_bug_generator.py
git commit -m "feat: generate jira-ready bug reports"
```

---

### Task 3: Bug CLI and local history

**Files:**
- Modify: `src/qanalisa/cli.py`
- Modify: `src/qanalisa/storage/workspace.py`
- Test: `tests/test_cli_bug.py`
- Test: `tests/storage/test_bug_history.py`

**Interfaces:**
- CLI: `qanalisa bug FN-1234`
- CLI: `qanalisa bug FN-1234 --full`
- Produces: `Workspace.save_bug(issue_key, report, full) -> Path`

- [ ] **Step 1: Write CLI prompt tests**

Use Typer's test runner with stdin containing a natural-language defect description. Assert short mode prints only the concise report body and full mode prints the structured report.

- [ ] **Step 2: Write bug-history test**

Saving two bugs must create two timestamped files under `.qa/FN-1234/bugs/` without overwriting the first.

- [ ] **Step 3: Implement CLI and persistence**

If `story.json` or `analysis.json` is missing, exit with a clear instruction to run `qanalisa FN-1234` first.

- [ ] **Step 4: Run plan suite**

Run: `pytest tests/test_cli_bug.py tests/storage/test_bug_history.py tests/analysis/test_bug_generator.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/qanalisa/cli.py src/qanalisa/storage/workspace.py tests/test_cli_bug.py tests/storage/test_bug_history.py
git commit -m "feat: add qanalisa bug workflow"
```
