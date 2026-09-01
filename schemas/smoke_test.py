"""Proves the three schemas hold together with fake data, and that the
built-in validation actually rejects bad input. Run this after any schema
change to make sure nothing silently broke.
"""

from datetime import date

from schemas.claim import Claim, EvidenceTier, SourceSpan, SourceType
from schemas.benchmark import Benchmark, RateBand, RequiredTerm
from schemas.result import BlockingItem, DimensionScore, Gap, Result

# --- one fake claim, T2 (project demonstrated) ---
claim = Claim(
    claim_id="clm_001",
    freelancer_id="fl_demo",
    text="Built and deployed a RAG pipeline serving 10k+ queries/day using Pinecone.",
    skill_ids=["skill_rag", "skill_vector_db"],
    source_type=SourceType.GITHUB,
    source_span=SourceSpan(
        document_id="doc_github_readme",
        start_index=120,
        end_index=195,
        extracted_text="Built and deployed a RAG pipeline serving 10k+ queries/day using Pinecone.",
    ),
    tier=EvidenceTier.T2,
    observed_date=date(2026, 3, 1),
    publishable=True,
)
assert claim.weight == 0.85, "T2 should auto-derive weight 0.85"
print("Claim OK ->", claim.claim_id, "tier", claim.tier, "weight", claim.weight)

# --- a fake benchmark for one niche ---
benchmark = Benchmark(
    niche="ai-engineering-freelance",
    required_terms=[
        RequiredTerm(term="vector database", synonyms=["pinecone", "weaviate", "qdrant", "chroma", "milvus"]),
        RequiredTerm(term="RAG", synonyms=["retrieval augmented generation"]),
    ],
    title_formula="{role} | {vertical} | {measurable outcome}",
    overview_words_min=150,
    overview_words_max=300,
    portfolio_min=3,
    rate_band=RateBand(min_hourly=45, max_hourly=120),
    dimension_targets={
        "positioning": 85,
        "evidence_quality": 80,
        "keyword_coverage": 90,
        "portfolio_quality": 85,
        "completeness": 95,
        "conversion": 75,
        "pricing_strategy": 80,
    },
    sample_size=30,
    built_date=date(2026, 9, 1),
)
print("Benchmark OK ->", benchmark.niche, len(benchmark.required_terms), "required terms")

# --- a fake result, evidence-capped ---
dims = {name: DimensionScore(current=30, target=85, weight=w) for name, w in {
    "positioning": 0.22,
    "evidence_quality": 0.22,
    "keyword_coverage": 0.15,
    "portfolio_quality": 0.15,
    "completeness": 0.10,
    "conversion": 0.08,
    "pricing_strategy": 0.08,
}.items()}

result = Result(
    freelancer_id="fl_demo",
    readiness=28,
    capped=True,
    dimensions=dims,
    blocking=[BlockingItem(description="No identity verification on file", reason="missing identity verification")],
    gaps=[Gap(dimension="evidence_quality", current=30, target=80, gain=11.0, effort_hours=4, priority=2.75)],
)
print("Result OK -> readiness", result.readiness, "capped", result.capped)

# --- prove validation actually rejects bad input, not just accepts good input ---
try:
    Result(freelancer_id="fl_demo", readiness=50, capped=False, dimensions={"positioning": DimensionScore(current=1, target=1, weight=1)})
    raise SystemExit("FAILED: Result should have rejected a dimensions dict missing 6 required dimensions")
except ValueError as e:
    print("Validation correctly rejected incomplete dimensions ->", e)

print("\nAll three schemas validated against fake data. Safe to build against these.")
