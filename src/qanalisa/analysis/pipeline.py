from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from time import perf_counter

from qanalisa.ai.provider import AIProvider
from qanalisa.analysis.dedupe import (
    dedupe_impacts,
    dedupe_scenarios,
    dedupe_text_items,
)
from qanalisa.analysis.plan_analyzer import PlanAnalyzer
from qanalisa.analysis.story_analyzer import StoryAnalyzer
from qanalisa.models import AnalysisMetadata, AnalysisResult, JiraIssue, KnowledgeMatch

ProgressCallback = Callable[[str, str, float | None], None]


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
        self.plan_analyzer = PlanAnalyzer(provider)

    @staticmethod
    def _notify(
        progress: ProgressCallback | None,
        stage: str,
        state: str,
        elapsed: float | None = None,
    ) -> None:
        if progress is not None:
            progress(stage, state, elapsed)

    def analyze(
        self,
        issue: JiraIssue,
        knowledge: KnowledgeMatch,
        *,
        knowledge_version: int,
        progress: ProgressCallback | None = None,
    ) -> AnalysisResult:
        self._notify(progress, "story", "start")
        started = perf_counter()
        facts = self.story_analyzer.analyze(issue)
        self._notify(progress, "story", "done", perf_counter() - started)

        self._notify(progress, "plan", "start")
        started = perf_counter()
        plan = self.plan_analyzer.analyze(issue, facts, knowledge)
        self._notify(progress, "plan", "done", perf_counter() - started)

        tests, seen = dedupe_scenarios(plan.tests)
        negative_tests, _ = dedupe_scenarios(plan.negative_tests, seen_titles=seen)
        negative_tests = [
            item.model_copy(update={"category": "exploratory"}) for item in negative_tests
        ]

        # Keep scenario IDs compact and stable after deterministic deduplication.
        all_scenarios = [*tests, *negative_tests]
        reindexed = [
            item.model_copy(update={"id": f"CT{index:02d}"})
            for index, item in enumerate(all_scenarios, start=1)
        ]
        tests = reindexed[: len(tests)]
        negative_tests = reindexed[len(tests) :]

        return AnalysisResult(
            issue_key=issue.key,
            context=facts.context,
            changes=dedupe_text_items(facts.changes),
            business_rules=dedupe_text_items(facts.business_rules),
            scope=dedupe_text_items(facts.scope),
            attention_points=dedupe_text_items(
                [*facts.attention_points, *plan.attention_points]
            ),
            erp_impacts=dedupe_impacts(plan.erp_impacts),
            tests=tests,
            negative_tests=negative_tests,
            regression=dedupe_text_items(plan.regression),
            questions=dedupe_text_items([*facts.questions, *plan.questions]),
            metadata=AnalysisMetadata(
                generated_at=datetime.now(timezone.utc).isoformat(),
                provider=self.provider_name,
                model=self.model,
                knowledge_version=knowledge_version,
                schema_version=2,
            ),
        )
