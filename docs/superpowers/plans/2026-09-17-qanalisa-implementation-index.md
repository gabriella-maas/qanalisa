# QAnalisa Implementation Index

The approved QAnalisa design is implemented through three independently testable plans.

1. `2026-09-17-qanalisa-core-analysis.md` — CLI bootstrap, Jira read-only integration, local workspace, Claude Code provider, VRSuper knowledge matching, structured analysis, Markdown output, cache/reanalysis.
2. `2026-09-17-qanalisa-test-bug-workflows.md` — scenario expansion and short/full bug-report workflows.
3. `2026-09-17-qanalisa-knowledge-lifecycle.md` — VRSuper knowledge show/add/update, documentation discovery, diffing, provenance, and atomic updates.

Execution order is 1 → 2 → 3. Each plan must leave the project passing its automated test suite before the next plan starts.
