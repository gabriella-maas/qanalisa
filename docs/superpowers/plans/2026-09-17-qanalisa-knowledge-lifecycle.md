# QAnalisa VRSuper Knowledge Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the VRSuper knowledge base inspectable, manually extensible, and refreshable from official documentation without overwriting curated QA knowledge.

**Architecture:** Keep documented and manual knowledge as separate source layers, merge them at load time, crawl/parse official documentation into a proposed documented snapshot, compute a human-readable diff, and atomically replace only the documented layer after successful validation.

**Tech Stack:** Existing QAnalisa stack plus BeautifulSoup4 for HTML parsing.

**Spec:** `docs/superpowers/specs/2026-09-17-qanalisa-design.md`

## Global Constraints

- Official source root: `https://docs.vrsoft.com.br/vrsuper`.
- Manual knowledge is never deleted by `knowledge update`.
- Every documented relationship retains its source URL.
- Failed update leaves the current knowledge files unchanged.
- The update pipeline must be testable against local HTML fixtures; normal tests do not crawl the internet.

---

### Task 1: Knowledge inspection and manual additions

**Files:**
- Modify: `src/qanalisa/knowledge/loader.py`
- Create: `src/qanalisa/knowledge/manual.py`
- Modify: `src/qanalisa/cli.py`
- Test: `tests/knowledge/test_manual.py`
- Test: `tests/test_cli_knowledge.py`

**Interfaces:**
- CLI: `qanalisa knowledge show Financeiro`
- CLI: `qanalisa knowledge add`
- Produces: `ManualKnowledgeStore.add(entry) -> None`

- [ ] **Step 1: Write merge test**

Create fixture knowledge where documented and manual relationships coexist; assert loader returns both and provenance remains distinct.

- [ ] **Step 2: Write manual-add persistence test**

Add a Financeiro → Recebimento relationship with `source_type: manual`; reload and assert it remains manual.

- [ ] **Step 3: Implement atomic manual store**

Write `manual.yaml` via temp-file replacement and validate with Pydantic before replacing.

- [ ] **Step 4: Add CLI `show` and interactive `add`**

`show` prints documented/manual relationships separately. `add` asks module, feature, related module, reason, and risks; it never asks for a fake documentation URL.

- [ ] **Step 5: Run tests and commit**

Run: `pytest tests/knowledge/test_manual.py tests/test_cli_knowledge.py -q`
Expected: PASS.

```bash
git add src/qanalisa/knowledge src/qanalisa/cli.py tests/knowledge/test_manual.py tests/test_cli_knowledge.py
git commit -m "feat: manage manual vrsuper knowledge"
```

---

### Task 2: Official documentation discovery and parsing

**Files:**
- Modify: `pyproject.toml`
- Create: `src/qanalisa/knowledge/docs_crawler.py`
- Create: `src/qanalisa/knowledge/docs_parser.py`
- Test fixtures: `tests/fixtures/vrsuper_docs/*.html`
- Test: `tests/knowledge/test_docs_parser.py`

**Interfaces:**
- Produces: `DocsCrawler.discover(root_url: str) -> list[str]`
- Produces: `DocsParser.parse(url: str, html: str) -> DocumentKnowledge`

- [ ] **Step 1: Add `beautifulsoup4>=4.12,<5` dependency**

Do not add a browser dependency; use httpx + HTML parsing only.

- [ ] **Step 2: Write parser tests from saved representative docs HTML**

Assert page title, breadcrumb/module labels, headings, body text, and same-site VRSuper links are extracted while nav/footer noise is ignored.

- [ ] **Step 3: Implement parser**

Normalize whitespace and preserve source URL. Parsing output is an intermediate document model, not final relationship truth.

- [ ] **Step 4: Write crawler discovery tests with `httpx.MockTransport`**

Assert it stays under the VRSuper docs root, deduplicates URLs, and respects a configurable page limit for safety.

- [ ] **Step 5: Implement crawler and run tests**

Run: `pytest tests/knowledge/test_docs_parser.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/qanalisa/knowledge/docs_crawler.py src/qanalisa/knowledge/docs_parser.py tests/fixtures/vrsuper_docs tests/knowledge/test_docs_parser.py
git commit -m "feat: parse official vrsuper documentation"
```

---

### Task 3: Claude-assisted relationship extraction with provenance

**Files:**
- Create: `src/qanalisa/knowledge/extractor.py`
- Test: `tests/knowledge/test_extractor.py`

**Interfaces:**
- Produces: `KnowledgeExtractor.extract(document: DocumentKnowledge) -> list[DocumentedKnowledgeEntry]`

- [ ] **Step 1: Define strict documented-entry schema**

Every entry requires source module/feature, related module/feature when present, reason, risks, `source_type="documented"`, and the originating URL.

- [ ] **Step 2: Write fake-provider extraction test**

Assert entries unsupported by the provided document text cannot be accepted as documented. The extraction prompt must instruct Claude to return no relationship rather than infer one.

- [ ] **Step 3: Implement extractor using `AIProvider.generate()`**

Use the same Claude CLI provider from the core plan with a dedicated JSON schema. Keep generic ERP inference out of this layer.

- [ ] **Step 4: Run tests and commit**

Run: `pytest tests/knowledge/test_extractor.py -q`
Expected: PASS.

```bash
git add src/qanalisa/knowledge/extractor.py tests/knowledge/test_extractor.py
git commit -m "feat: extract documented vrsuper relationships"
```

---

### Task 4: Diff, validation, and atomic documented update

**Files:**
- Create: `src/qanalisa/knowledge/diff.py`
- Create: `src/qanalisa/knowledge/updater.py`
- Test: `tests/knowledge/test_diff.py`
- Test: `tests/knowledge/test_updater.py`

**Interfaces:**
- Produces: `KnowledgeDiff(added, changed, removed)`
- Produces: `KnowledgeUpdater.build_update() -> tuple[KnowledgeDiff, KnowledgeBase]`
- Produces: `KnowledgeUpdater.apply(candidate) -> None`

- [ ] **Step 1: Write diff tests**

Assert added/changed/removed documented entries are identified by stable identity, while manual entries are absent from the removal calculation.

- [ ] **Step 2: Implement deterministic diff**

Sort output for stable terminal rendering and tests.

- [ ] **Step 3: Write atomic-failure test**

Simulate failure after candidate generation but before replacement; assert original documented files and `metadata.json` are byte-for-byte unchanged.

- [ ] **Step 4: Implement candidate directory + atomic replacement**

Validate all candidate YAML/JSON before replacing documented files. Update metadata only in the same successful apply operation.

- [ ] **Step 5: Run tests and commit**

Run: `pytest tests/knowledge/test_diff.py tests/knowledge/test_updater.py -q`
Expected: PASS.

```bash
git add src/qanalisa/knowledge/diff.py src/qanalisa/knowledge/updater.py tests/knowledge/test_diff.py tests/knowledge/test_updater.py
git commit -m "feat: safely refresh documented knowledge"
```

---

### Task 5: `qanalisa knowledge update` CLI

**Files:**
- Modify: `src/qanalisa/cli.py`
- Test: `tests/test_cli_knowledge_update.py`

**Interfaces:**
- CLI: `qanalisa knowledge update`

- [ ] **Step 1: Write CLI test using mocked updater**

Assert output includes counts for added/changed/removed entries, preserves manual knowledge message, and prints new knowledge version after apply.

- [ ] **Step 2: Implement CLI flow**

Flow: discover docs → parse → extract documented entries → build candidate → show diff → apply. If any stage raises, show a concise error and state that the existing base was preserved.

- [ ] **Step 3: Run complete knowledge suite**

Run: `pytest tests/knowledge tests/test_cli_knowledge.py tests/test_cli_knowledge_update.py -q`
Expected: PASS without internet access.

- [ ] **Step 4: Manual live update smoke test**

On a networked development machine with Claude authenticated:

```bash
qanalisa knowledge update
```

Verify source URLs belong to official VRSuper docs, manual entries remain unchanged, and metadata version increments only after a successful update.

- [ ] **Step 5: Commit**

```bash
git add src/qanalisa/cli.py tests/test_cli_knowledge_update.py
git commit -m "feat: add vrsuper knowledge update command"
```
