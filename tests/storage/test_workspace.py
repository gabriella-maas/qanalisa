from pathlib import Path

from qanalisa.models import AnalysisMetadata, AnalysisResult, JiraIssue
from qanalisa.storage.workspace import Workspace


def test_story_roundtrip(tmp_path: Path):
    ws = Workspace(tmp_path / ".qa")
    issue = JiraIssue(key="FN-14", title="Teste", description="Descrição")
    ws.save_story(issue)
    assert ws.load_story("FN-14") == issue


def test_analysis_metadata_roundtrip(tmp_path: Path):
    ws = Workspace(tmp_path / ".qa")
    analysis = AnalysisResult(
        issue_key="FN-14",
        context="Contexto",
        metadata=AnalysisMetadata(
            generated_at="2026-09-17T10:00:00-03:00",
            provider="claude_cli",
            model="sonnet",
            knowledge_version=3,
            schema_version=1,
        ),
    )
    ws.save_analysis("FN-14", analysis)

    loaded = ws.load_analysis("FN-14")
    assert loaded == analysis
    assert loaded is not None
    assert loaded.metadata.provider == "claude_cli"
    assert loaded.metadata.knowledge_version == 3
