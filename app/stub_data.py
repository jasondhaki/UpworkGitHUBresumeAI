"""Fake claims + benchmark, used only until real ingestion (Phase B) replaces them.
Deliberately the exact shapes real data will arrive in, so swapping this out later
is a data-source change, not a schema change.
"""

from datetime import date

from schemas.benchmark import Benchmark, RateBand, RequiredTerm
from schemas.claim import Claim, EvidenceTier, SourceType

STUB_BENCHMARK = Benchmark(
    niche="ai-engineering-freelance",
    required_terms=[
        RequiredTerm(term="vector database", synonyms=["pinecone", "weaviate", "qdrant", "chroma", "milvus"]),
        RequiredTerm(term="RAG", synonyms=["retrieval augmented generation"]),
        RequiredTerm(term="LLM fine-tuning", synonyms=["fine-tune", "fine-tuning"]),
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

STUB_MANUAL_SCORES = {
    "positioning": 55.0,
    "portfolio_quality": 60.0,
    "completeness": 70.0,
    "conversion": 40.0,
    "pricing_strategy": 50.0,
}


def stub_github_claim(github_username: str) -> list[Claim]:
    """GitHub API pull isn't built yet — Phase B. CV and Upwork-paste are real now
    (see app.ingestion.cv_parser / app.ingestion.upwork_parser)."""
    if not github_username.strip():
        return []
    return [
        Claim(
            claim_id="stub_github_1",
            freelancer_id="fl_stub",
            text=f"GitHub profile: {github_username.strip()} (stub — not yet pulled via API)",
            skill_ids=["skill_stub_github"],
            source_type=SourceType.GITHUB,
            tier=EvidenceTier.T2,
            observed_date=date(2026, 9, 1),
            publishable=True,
        )
    ]
