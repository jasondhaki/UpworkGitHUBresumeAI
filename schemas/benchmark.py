from datetime import date

from pydantic import BaseModel, Field

# The seven scoring dimensions from Section 2, spelled the same way everywhere in the codebase.
DIMENSIONS = (
    "positioning",
    "evidence_quality",
    "keyword_coverage",
    "portfolio_quality",
    "completeness",
    "conversion",
    "pricing_strategy",
)


class RequiredTerm(BaseModel):
    """One term the benchmark expects to see, plus known aliases.

    synonyms exists because generic embedding similarity doesn't reliably know
    "Pinecone" is a vector database (tested and confirmed unreliable — see the
    implementation note under Section 2 in PROJECT_PLAN.md). For a known term,
    check synonyms first; only fall back to embeddings for free-text matches
    with no fixed alias list.
    """

    term: str
    synonyms: list[str] = Field(default_factory=list)


class RateBand(BaseModel):
    currency: str = "USD"
    min_hourly: float
    max_hourly: float


class Benchmark(BaseModel):
    niche: str
    required_terms: list[RequiredTerm]
    title_formula: str
    overview_words_min: int
    overview_words_max: int
    portfolio_min: int
    rate_band: RateBand
    # benchmark_target per dimension (Section 2's gap-ranking formula) — what the top tier
    # actually reaches, not a perfect 100. Keys must be exactly the DIMENSIONS names above.
    dimension_targets: dict[str, float]
    sample_size: int  # profiles this was hand-read from; capped at 30 (Section 5). 0 = not sampled yet.
    built_date: date
    # True until the real 30-profile hand-read (Section 5) replaces this benchmark's values.
    # A structural flag, not just a comment, so the app itself can show the caveat to users
    # instead of relying on whoever's reading the source to notice it.
    provisional: bool = False
    source_notes: str = ""  # what this was actually built from, and what would upgrade it
