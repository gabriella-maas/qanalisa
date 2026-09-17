from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from qanalisa.models import AnalysisResult, FullBugReport, JiraIssue, ShortBugReport


class Workspace:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _issue_dir(self, issue_key: str) -> Path:
        return self.root / issue_key.upper()

    @staticmethod
    def _atomic_write_json(path: Path, payload: dict) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def save_story(self, issue: JiraIssue) -> Path:
        path = self._issue_dir(issue.key) / "story.json"
        return self._atomic_write_json(path, issue.model_dump(mode="json"))

    def load_story(self, issue_key: str) -> JiraIssue | None:
        path = self._issue_dir(issue_key) / "story.json"
        if not path.exists():
            return None
        return JiraIssue.model_validate_json(path.read_text(encoding="utf-8"))

    def save_analysis(self, issue_key: str, analysis: AnalysisResult) -> Path:
        path = self._issue_dir(issue_key) / "analysis.json"
        return self._atomic_write_json(path, analysis.model_dump(mode="json"))

    def load_analysis(self, issue_key: str) -> AnalysisResult | None:
        path = self._issue_dir(issue_key) / "analysis.json"
        if not path.exists():
            return None
        return AnalysisResult.model_validate_json(path.read_text(encoding="utf-8"))
    def save_markdown(self, issue_key: str, markdown: str) -> Path:
        path = self._issue_dir(issue_key) / f"analise-{issue_key.upper()}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(markdown, encoding="utf-8")
        temporary.replace(path)
        return path
    def save_bug(
        self,
        issue_key: str,
        report: ShortBugReport | FullBugReport,
        *,
        full: bool,
    ) -> Path:
        bug_dir = self._issue_dir(issue_key) / "bugs"
        bug_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        suffix = "full" if full else "short"
        path = bug_dir / f"bug-{stamp}-{suffix}.md"

        if isinstance(report, ShortBugReport):
            text = report.text.rstrip() + "\n"
        else:
            preconditions = "\n".join(f"- {item}" for item in report.preconditions)
            steps = "\n".join(
                f"{index}. {item}" for index, item in enumerate(report.steps, start=1)
            )
            evidence = "\n".join(f"- {item}" for item in report.evidence)
            text = (
                f"# {report.title}\n\n"
                f"## Pré-condições\n{preconditions}\n\n"
                f"## Passos para reproduzir\n{steps}\n\n"
                f"## Resultado atual\n{report.actual_result}\n\n"
                f"## Resultado esperado\n{report.expected_result}\n\n"
                f"## Evidências\n{evidence}\n\n"
                f"## Impacto\n{report.impact}\n"
            )

        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(path)
        return path

