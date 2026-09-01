"""Tests blocking-item detection with fake claims. No Gemini calls."""

from datetime import date

from schemas.benchmark import Benchmark, RateBand, RequiredTerm
from schemas.claim import Claim, EvidenceTier, SourceType

from app.scoring.blocking import detect_blocking_items
from app.scoring.engine import score_profile

BENCHMARK = Benchmark(
    niche="ai-engineering-freelance",
    required_terms=[
        RequiredTerm(term="RAG", synonyms=["retrieval augmented generation"]),
        RequiredTerm(term="vector database", synonyms=["pinecone"]),
    ],
    title_formula="{role} | {vertical} | {measurable outcome}",
    overview_words_min=150, overview_words_max=300, portfolio_min=3,
    rate_band=RateBand(min_hourly=45, max_hourly=120),
    dimension_targets={n: 85 for n in ("positioning", "evidence_quality", "keyword_coverage",
                                        "portfolio_quality", "completeness", "conversion", "pricing_strategy")},
    sample_size=0, built_date=date(2026, 9, 2),
)


def claim(claim_id, tier, text):
    return Claim(claim_id=claim_id, freelancer_id="fl_test", text=text, skill_ids=[],
                 source_type=SourceType.CV, tier=tier, observed_date=date(2026, 9, 1), publishable=True)


print("=== Case 1: RAG claimed only via self-declaration (T8) -> should be flagged unproven ===")
claims1 = [claim("c1", EvidenceTier.T8, "I know RAG well.")]
items1 = detect_blocking_items(claims1, BENCHMARK)
print([i.reason for i in items1])
assert any(i.reason == "missing identity verification" for i in items1), "identity verification should always be flagged in Phase 1"
assert any(i.reason == "unproven claim" and "RAG" in i.description for i in items1), "self-declared-only RAG claim should be flagged"

print("\n=== Case 2: RAG backed by real evidence (T2) -> should NOT be flagged as unproven ===")
claims2 = [
    claim("c2", EvidenceTier.T2, "Built and deployed a RAG pipeline."),
    claim("c3", EvidenceTier.T8, "I also mention RAG here casually."),  # weaker duplicate, shouldn't matter
]
items2 = detect_blocking_items(claims2, BENCHMARK)
print([i.reason for i in items2])
assert not any(i.reason == "unproven claim" for i in items2), "strongest evidence for RAG is T2, should not be flagged"
assert len(items2) == 1, "only the always-present identity-verification item should remain"

print("\n=== Case 3: wired into score_profile by default (no override) ===")
result = score_profile("fl_test", claims1, BENCHMARK)
print("blocking items in result:", [i.reason for i in result.blocking])
assert len(result.blocking) >= 2, "score_profile should auto-populate blocking, not leave it empty"

print("\n=== Case 4: explicit override still works (empty list forces no auto-detection) ===")
result_override = score_profile("fl_test", claims1, BENCHMARK, blocking=[])
assert result_override.blocking == [], "explicit blocking=[] should bypass auto-detection"

print("\nAll blocking-detection checks passed. No Gemini calls made.")
