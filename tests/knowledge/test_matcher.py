from qanalisa.knowledge.matcher import KnowledgeMatcher
from qanalisa.models import (
    KnowledgeBase,
    KnowledgeFeature,
    KnowledgeModule,
    KnowledgeRelationship,
    KnowledgeRisk,
)


def _knowledge() -> KnowledgeBase:
    return KnowledgeBase(
        version=1,
        modules=[
            KnowledgeModule(
                name="Financeiro",
                aliases=["financeiro"],
                features=[
                    KnowledgeFeature(
                        name="Conta a Pagar",
                        aliases=["conta a pagar", "contas a pagar"],
                        keywords=["título", "titulo", "desconto"],
                        source_type="documented",
                    )
                ],
            )
        ],
        relationships=[
            KnowledgeRelationship(
                from_module="Financeiro",
                from_feature="Conta a Pagar",
                to_module="Venda",
                to_feature="Devolução de Cliente",
                reason="Títulos também podem ser gerados por devoluções de clientes.",
                provenance="documented",
            )
        ],
        risks=[
            KnowledgeRisk(
                module="Financeiro",
                feature="Conta a Pagar",
                text="Validar totalizadores e situação dos títulos.",
                provenance="documented",
            )
        ],
    )


def test_matcher_finds_financeiro_conta_a_pagar():
    match = KnowledgeMatcher(_knowledge()).match(
        "Registrar desconto no título de Contas a Pagar do Financeiro"
    )

    assert match.module == "Financeiro"
    assert match.feature == "Conta a Pagar"
    assert match.confidence > 0.5
    assert match.relationships[0].provenance == "documented"
    assert match.risks[0].provenance == "documented"


def test_matcher_returns_low_confidence_no_match_instead_of_inventing():
    match = KnowledgeMatcher(_knowledge()).match("Alterar uma rotina sem relação cadastrada")

    assert match.module is None
    assert match.feature is None
    assert match.confidence == 0.0
    assert match.relationships == []
    assert match.risks == []
