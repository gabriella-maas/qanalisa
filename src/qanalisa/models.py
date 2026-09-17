from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Provenance = Literal["story", "documented", "manual", "inferred", "unknown"]
Priority = Literal["P0", "P1", "P2", "P3"]


class JiraIssue(BaseModel):
    key: str
    title: str
    description: str


class AnalysisMetadata(BaseModel):
    generated_at: str
    provider: str
    model: str | None = None
    knowledge_version: int
    schema_version: int = 1


class TextItem(BaseModel):
    text: str
    provenance: Provenance = "unknown"


class ErpImpact(BaseModel):
    module: str
    reason: str
    provenance: Provenance = "inferred"


class TestScenario(BaseModel):
    id: str
    title: str
    priority: Priority = "P1"
    provenance: Provenance = "inferred"
    related_risks: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    issue_key: str
    context: str
    changes: list[TextItem] = Field(default_factory=list)
    business_rules: list[TextItem] = Field(default_factory=list)
    scope: list[TextItem] = Field(default_factory=list)
    attention_points: list[TextItem] = Field(default_factory=list)
    erp_impacts: list[ErpImpact] = Field(default_factory=list)
    tests: list[TestScenario] = Field(default_factory=list)
    negative_tests: list[TestScenario] = Field(default_factory=list)
    regression: list[TextItem] = Field(default_factory=list)
    questions: list[TextItem] = Field(default_factory=list)
    metadata: AnalysisMetadata


class KnowledgeFeature(BaseModel):
    name: str
    aliases: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    source_type: Provenance = "documented"
    source_ids: list[str] = Field(default_factory=list)


class KnowledgeModule(BaseModel):
    name: str
    aliases: list[str] = Field(default_factory=list)
    features: list[KnowledgeFeature] = Field(default_factory=list)


class KnowledgeRelationship(BaseModel):
    from_module: str
    from_feature: str | None = None
    to_module: str
    to_feature: str | None = None
    reason: str
    provenance: Provenance = "documented"
    source_ids: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class KnowledgeRisk(BaseModel):
    module: str
    feature: str | None = None
    text: str
    provenance: Provenance = "documented"
    source_ids: list[str] = Field(default_factory=list)


class KnowledgeSource(BaseModel):
    id: str
    title: str
    url: str


class KnowledgeBase(BaseModel):
    version: int
    modules: list[KnowledgeModule] = Field(default_factory=list)
    relationships: list[KnowledgeRelationship] = Field(default_factory=list)
    risks: list[KnowledgeRisk] = Field(default_factory=list)
    sources: list[KnowledgeSource] = Field(default_factory=list)
    last_update: str | None = None


class KnowledgeMatch(BaseModel):
    module: str | None = None
    feature: str | None = None
    confidence: float = 0.0
    relationships: list[KnowledgeRelationship] = Field(default_factory=list)
    risks: list[KnowledgeRisk] = Field(default_factory=list)


class StoryFacts(BaseModel):
    context: str
    changes: list[TextItem] = Field(default_factory=list)
    business_rules: list[TextItem] = Field(default_factory=list)
    scope: list[TextItem] = Field(default_factory=list)
    attention_points: list[TextItem] = Field(default_factory=list)
    module_candidates: list[str] = Field(default_factory=list)
    feature_candidates: list[str] = Field(default_factory=list)
    questions: list[TextItem] = Field(default_factory=list)


class ImpactAnalysis(BaseModel):
    erp_impacts: list[ErpImpact] = Field(default_factory=list)
    regression: list[TextItem] = Field(default_factory=list)
    attention_points: list[TextItem] = Field(default_factory=list)


class GeneratedTests(BaseModel):
    tests: list[TestScenario] = Field(default_factory=list)
    negative_tests: list[TestScenario] = Field(default_factory=list)
    regression: list[TextItem] = Field(default_factory=list)
    questions: list[TextItem] = Field(default_factory=list)


class DetailedTestCase(BaseModel):
    id: str
    title: str
    priority: Priority = "P1"
    objective: str
    preconditions: list[str] = Field(default_factory=list)
    steps: list[str] = Field(min_length=1)
    expected_result: str = Field(min_length=1)
    related_risks: list[str] = Field(default_factory=list)


class ShortBugReport(BaseModel):
    text: str = Field(min_length=1)


class FullBugReport(BaseModel):
    title: str = Field(min_length=1)
    preconditions: list[str] = Field(min_length=1)
    steps: list[str] = Field(min_length=1)
    actual_result: str = Field(min_length=1)
    expected_result: str = Field(min_length=1)
    evidence: list[str] = Field(min_length=1)
    impact: str = Field(min_length=1)
