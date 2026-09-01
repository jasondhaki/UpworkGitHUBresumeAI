"""Proves the scoring engine end to end on fake claims, now that all seven
dimensions have real formulas. Cases: real evidence + generated content,
fully self-declared (both caps), and pricing_strategy specifically (rate vs.
evidence strength, with and without a stated rate).
"""

from datetime import date

from schemas.benchmark import Benchmark, RateBand, RequiredTerm
from schemas.claim import Claim, EvidenceTier, SourceType
from schemas.result import GeneratedContent, GeneratedField, SourceSpanRef

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
        "positioning": 85, "evidence_quality": 80, "keyword_coverage": 90,
        "portfolio_quality": 85, "completeness": 95, "conversion": 75, "pricing_strategy": 80,
    },
    sample_size=30,
    built_date=date(2026, 9, 1),
)


def make_claim(tier: EvidenceTier, text: str, skill_ids: list[str], source_type=SourceType.GITHUB) -> Claim:
    return Claim(
        claim_id=f"clm_{tier.value}_{text[:8]}",
        freelancer_id="fl_demo", text=text, skill_ids=skill_ids, source_type=source_type,
        tier=tier, observed_date=date(2026, 3, 1), publishable=True,
    )


print("=== Case 1: real evidence across all three sources, with generated content ===")
claims_real = [
    make_claim(EvidenceTier.T2, "Built and deployed a RAG pipeline using Pinecone, serving 10k queries/day.",
               ["skill_rag"], source_type=SourceType.GITHUB),
    make_claim(EvidenceTier.T6, "Fine-tuned an LLM at a previous employer for classification.",
               ["skill_ft"], source_type=SourceType.CV),
    make_claim(EvidenceTier.T1, 'One client wrote, "saved us thousands of dollars."',
               ["skill_client"], source_type=SourceType.UPWORK_PASTE),
]
generated = GeneratedContent(
    title=GeneratedField(text="AI Engineer | RAG Systems | 10k queries/day", source_spans=[SourceSpanRef(claim_id="x", document_id="d", start_index=0, end_index=1)]),
    overview=GeneratedField(text="You need reliable RAG systems that scale. I built a pipeline serving 10k queries/day for a past client.", source_spans=[]),
)
result1 = score_profile("fl_demo_1", claims_real, BENCHMARK, generated=generated, stated_rate=90)
print("readiness:", result1.readiness, "| capped:", result1.capped)
for name, d in result1.dimensions.items():
    print(f"  {name:18} {d.current:5.1f} / target {d.target}")
assert not result1.capped
assert result1.dimensions["completeness"].current > 0, "completeness should reflect the checklist items present"
assert result1.dimensions["portfolio_quality"].current > 0, "T1/T2 claims should count as portfolio items"
assert result1.dimensions["positioning"].current > 0, "generated title/overview should produce a positioning score"

print("\n=== Case 2: everything self-declared (T8 only), no generation, no rate ===")
claims_self_declared = [
    make_claim(EvidenceTier.T8, "I know Python.", ["skill_python"]),
    make_claim(EvidenceTier.T8, "I know RAG.", ["skill_rag"]),
]
result2 = score_profile("fl_demo_2", claims_self_declared, BENCHMARK)
print("readiness:", result2.readiness, "| capped:", result2.capped)
assert result2.capped and result2.readiness <= 30
assert result2.dimensions["positioning"].current == 0.0, "no generated content -> positioning proxy scores 0"
assert result2.dimensions["pricing_strategy"].current == 0.0, "no stated rate -> pricing_strategy scores 0"

print("\n=== Case 3: pricing_strategy, thin evidence + a rate near the top of the band ===")
score_low_evidence_high_rate = score_profile("fl_demo_3", claims_self_declared, BENCHMARK, stated_rate=118)
score_low_evidence_low_rate = score_profile("fl_demo_4", claims_self_declared, BENCHMARK, stated_rate=48)
print("thin evidence, rate near max:", score_low_evidence_high_rate.dimensions["pricing_strategy"].current)
print("thin evidence, modest rate:  ", score_low_evidence_low_rate.dimensions["pricing_strategy"].current)
assert score_low_evidence_low_rate.dimensions["pricing_strategy"].current > score_low_evidence_high_rate.dimensions["pricing_strategy"].current, \
    "a modest rate should be more 'defensible' than a top-of-band rate when evidence is thin"

print("\nAll scoring engine checks passed.")
