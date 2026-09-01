from pydantic import BaseModel, Field

from .benchmark import DIMENSIONS


class DimensionScore(BaseModel):
    current: float  # this profile's score on this dimension, 0-100
    target: float  # the benchmark_target for this dimension, copied in for display
    weight: float  # this dimension's share of the overall score (Section 2 weights, sum to 1.0)


class BlockingItem(BaseModel):
    """A liability, not an optimization opportunity — never enters the ranked gap list (Section 3)."""

    description: str
    reason: str  # e.g. "unproven claim", "ToS risk", "missing identity verification"


class Gap(BaseModel):
    dimension: str
    current: float
    target: float
    gain: float
    effort_hours: float
    priority: float


class SourceSpanRef(BaseModel):
    """Which claim + source span backs one traced number in generated text."""

    claim_id: str
    document_id: str
    start_index: int
    end_index: int


class GeneratedField(BaseModel):
    text: str
    source_spans: list[SourceSpanRef] = Field(default_factory=list)


class GeneratedContent(BaseModel):
    title: GeneratedField | None = None
    overview: GeneratedField | None = None


class Result(BaseModel):
    freelancer_id: str
    readiness: int  # 0-100, final score after both caps applied
    capped: bool  # True if the evidence cap (Section 2: score capped at 30 when evidence is all self-declared)
    dimensions: dict[str, DimensionScore]  # keys must be exactly the DIMENSIONS names
    blocking: list[BlockingItem] = Field(default_factory=list)
    gaps: list[Gap] = Field(default_factory=list)  # ranked; blocking items never appear here
    generated: GeneratedContent = Field(default_factory=GeneratedContent)

    def model_post_init(self, __context) -> None:
        missing = set(DIMENSIONS) - set(self.dimensions)
        if missing:
            raise ValueError(f"result is missing dimensions: {missing}")
