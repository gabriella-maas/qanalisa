from pathlib import Path

from qanalisa.models import FullBugReport, ShortBugReport
from qanalisa.storage.workspace import Workspace


def test_save_bug_creates_timestamped_history_without_overwrite(tmp_path: Path):
    ws = Workspace(tmp_path / ".qa")
    first = ws.save_bug("FN-14", ShortBugReport(text="Primeiro bug"), full=False)
    second = ws.save_bug(
        "FN-14",
        FullBugReport(
            title="Segundo bug",
            preconditions=["Não informado"],
            steps=["Executar ação"],
            actual_result="Falha",
            expected_result="Sucesso",
            evidence=["Não informado"],
            impact="Fluxo bloqueado",
        ),
        full=True,
    )

    assert first.exists()
    assert second.exists()
    assert first != second
    assert first.parent == tmp_path / ".qa" / "FN-14" / "bugs"
    assert second.parent == first.parent
    assert first.read_text(encoding="utf-8") == "Primeiro bug\n"
    assert "## Resultado atual" in second.read_text(encoding="utf-8")
    assert len(list(first.parent.glob("bug-*.md"))) == 2
