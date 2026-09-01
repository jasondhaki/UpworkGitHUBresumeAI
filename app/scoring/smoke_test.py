"""Proves the scoring engine end to end on fake claims. Two cases:
a profile with real evidence, and one that's entirely self-declared (should
hit both the per-dimension and overall-readiness caps from Section 2).
"""

from datetime import date

from schemas.benchmark import Benchmark, RateBand, RequiredTerm
from schemas.claim import Claim, EvidenceTier, SourceType

from app.scoring.engine import score_profile

BENCHMARK = Benchmark(
    niche="ai-engineering-freelance",
    required_terms=[
        RequiredTerm(term="vector database", synonyms=["pinecone", "weaviate", "qdrant"]),
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

MANUAL_SCORES = {  # stand-ins for the 5 dimensions without a formula yet (see engine.py docstring)
    "positioning": 55.0,
    "portfolio_quality": 60.0,
    "completeness": 70.0,
    "conversion": 40.0,
    "pricing_strategy": 50.0,
}


def make_claim(tier: EvidenceTier, text: str, skill_ids: list[str]) -> Claim:
    return Claim(
        claim_id=f"clm_{tier.value}_{text[:8]}",
        freelancer_id="fl_demo",
        text=text,
        skill_ids=skill_ids,
        source_type=SourceType.GITHUB,
        tier=tier,
        observed_date=date(2026, 3, 1),
        publishable=True,
    )


print("=== Case 1: real evidence, mixed tiers ===")
claims_real = [
    make_claim(EvidenceTier.T2, "Built and deployed a RAG pipeline using Pinecone for retrieval.", ["skill_rag"]),
    make_claim(EvidenceTier.T6, "Fine-tuned an LLM at a previous employer for classification.", ["skill_ft"]),
    make_claim(EvidenceTier.T8, "Comfortable with vector databases.", ["skill_vecdb"]),
]
result1 = score_profile("fl_demo_1", claims_real, BENCHMARK, MANUAL_SCORES)
print("readiness:", result1.readiness, "| capped:", result1.capped)
print("evidence_quality:", round(result1.dimensions["evidence_quality"].current, 1))
print("keyword_coverage:", round(result1.dimensions["keyword_coverage"].current, 1))
print("top gaps:")
for g in result1.gaps:
    print(f"  {g.dimension:18} current={g.current:5.1f} target={g.target:5.1f} gain={g.gain:5.2f} priority={g.priority:5.2f}")
assert not result1.capped, "profile with real evidence should not hit the self-declared cap"

print("\n=== Case 2: everything self-declared (T8 only) ===")
claims_self_declared = [
    make_claim(EvidenceTier.T8, "I know Python.", ["skill_python"]),
    make_claim(EvidenceTier.T8, "I know RAG.", ["skill_rag"]),
]
result2 = score_profile("fl_demo_2", claims_self_declared, BENCHMARK, MANUAL_SCORES)
print("readiness:", result2.readiness, "| capped:", result2.capped)
print("evidence_quality:", round(result2.dimensions["evidence_quality"].current, 1))
assert result2.capped, "all-T8 profile should trigger the cap"
assert result2.readiness <= 30, f"capped readiness should be <= 30, got {result2.readiness}"
assert result2.dimensions["evidence_quality"].current <= 30, "evidence_quality dimension should also be capped at 30"

print("\nAll scoring engine checks passed.")
