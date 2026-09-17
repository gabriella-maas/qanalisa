from qanalisa.analysis.story_analyzer import StoryAnalyzer
from qanalisa.models import JiraIssue


class FakeProvider:
    def __init__(self):
        self.prompts = []
        self.schemas = []

    def generate(self, prompt: str, schema: dict) -> dict:
        self.prompts.append(prompt)
        self.schemas.append(schema)
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


def test_story_analyzer_validates_structured_story_facts():
    provider = FakeProvider()
    analyzer = StoryAnalyzer(provider)
    issue = JiraIssue(
        key="FN-14",
        title="Registrar desconto de contrato",
        description="O desconto deve ser registrado em Acordo Comercial.",
    )

    facts = analyzer.analyze(issue)

    assert facts.context == "Registrar desconto de contrato em acordo comercial"
    assert facts.changes[0].provenance == "story"
    assert facts.module_candidates == ["Financeiro"]
    assert "[STAGE:story]" in provider.prompts[0]
    assert "não invente" in provider.prompts[0].lower()
