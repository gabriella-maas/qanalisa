from pathlib import Path

from qanalisa.knowledge.loader import KnowledgeLoader
from qanalisa.knowledge.matcher import KnowledgeMatcher


def test_vrsuper_conta_a_pagar_has_documented_nf_and_baixa_relationships():
    root = Path(__file__).resolve().parents[2] / "knowledge" / "vrsuper"
    knowledge = KnowledgeLoader(root).load()
    match = KnowledgeMatcher(knowledge).match(
        "Registrar desconto no Financeiro em título de Contas a Pagar gerado por Nota Fiscal"
    )

    assert knowledge.version >= 2
    assert match.module == "Financeiro"
    assert match.feature == "Conta a Pagar"

    targets = {(item.to_module, item.to_feature, item.provenance) for item in match.relationships}
    assert ("Fiscal", "Recebimento de Nota Fiscal", "documented") in targets
    assert ("Financeiro", "Baixa de Título", "documented") in targets
    assert any(risk.provenance == "inferred" for risk in match.risks)
