from __future__ import annotations

from datetime import datetime, timezone

from qanalisa.ai.provider import AIProvider
from qanalisa.analysis.impact_analyzer import ImpactAnalyzer
from qanalisa.analysis.story_analyzer import StoryAnalyzer
from qanalisa.analysis.test_generator import TestGenerator
from qanalisa.models import AnalysisMetadata, AnalysisResult, JiraIssue, KnowledgeMatch


class AnalysisPipeline:
    def __init__(
        self,
        provider: AIProvider,
        *,
        provider_name: str = "claude_cli",
        model: str | None = None,
    ) -> None:
        self.provider = provider
        self.provider_name = provider_name
        self.model = model
        self.story_analyzer = StoryAnalyzer(provider)
        self.impact_analyzer = ImpactAnalyzer(provider)
        self.test_generator = TestGenerator(provider)

    def analyze(
        self,
        issue: JiraIssue,
        knowledge: KnowledgeMatch,
        *,
        knowledge_version: int,
    ) -> AnalysisResult:
        facts = self.story_analyzer.analyze(issue)
        impact = self.impact_analyzer.analyze(issue, facts, knowledge)
        tests = self.test_generator.generate(issue, facts, impact)

        return AnalysisResult(
            issue_key=issue.key,
            context=facts.context,
            changes=facts.changes,
            business_rules=facts.business_rules,
            scope=facts.scope,
            attention_points=[*facts.attention_points, *impact.attention_points],
            erp_impacts=impact.erp_impacts,
            tests=tests.tests,
            negative_tests=tests.negative_tests,
            regression=tests.regression or impact.regression,
            questions=[*facts.questions, *tests.questions],
            metadata=AnalysisMetadata(
                generated_at=datetime.now(timezone.utc).isoformat(),
                provider=self.provider_name,
                model=self.model,
                knowledge_version=knowledge_version,
                schema_version=1,
            ),
        )
