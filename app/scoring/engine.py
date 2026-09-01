"""Ties dimensions.py + gap_ranking.py together into a Result.

score_profile() is the one function the rest of the app calls. The
`manual_dimension_scores` argument exists only because five of the seven
dimensions don't have a formula yet (see dimensions.py) — Phase A proves the
aggregation math (weights, both caps, gap ranking, dependency gating) works
end to end, using real formulas for the two dimensions that have one and
placeholder inputs for the rest. As real logic lands for each remaining
dimension, delete its entry from `manual_dimension_scores` callers pass in.
"""

from schemas.benchmark import DIMENSIONS, Benchmark
from schemas.claim import Claim
from schemas.result import BlockingItem, DimensionScore, GeneratedContent, Result

from .dimensions import compute_evidence_quality, compute_keyword_coverage
from .gap_ranking import compute_gaps, select_top_five

DIMENSION_WEIGHTS: dict[str, float] = {
    "positioning": 0.22,
    "evidence_quality": 0.22,
    "keyword_coverage": 0.15,
    "portfolio_quality": 0.15,
    "completeness": 0.10,
    "conversion": 0.08,
    "pricing_strategy": 0.08,
}
assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 1e-9, "dimension weights must sum to 1.0"

OVERALL_SELF_DECLARED_CAP = 30  # Section 2: overall readiness capped at 30 when every claim is self-declared


def score_profile(
    freelancer_id: str,
    claims: list[Claim],
    benchmark: Benchmark,
    manual_dimension_scores: dict[str, float],
    blocking: list[BlockingItem] | None = None,
) -> Result:
    evidence_score, all_self_declared = compute_evidence_quality(claims)
    keyword_score = compute_keyword_coverage(claims, benchmark)

    raw_scores = {
        "positioning": manual_dimension_scores.get("positioning", 0.0),
        "evidence_quality": evidence_score,
        "keyword_coverage": keyword_score,
        "portfolio_quality": manual_dimension_scores.get("portfolio_quality", 0.0),
        "completeness": manual_dimension_scores.get("completeness", 0.0),
        "conversion": manual_dimension_scores.get("conversion", 0.0),
        "pricing_strategy": manual_dimension_scores.get("pricing_strategy", 0.0),
    }

    dimensions: dict[str, DimensionScore] = {
        name: DimensionScore(
            current=raw_scores[name],
            target=benchmark.dimension_targets.get(name, 100.0),
            weight=DIMENSION_WEIGHTS[name],
        )
        for name in DIMENSIONS
    }

    weighted_sum = sum(d.current * d.weight for d in dimensions.values())
    readiness = round(weighted_sum)
    if all_self_declared:
        readiness = min(readiness, OVERALL_SELF_DECLARED_CAP)

    all_gaps = compute_gaps(dimensions)
    top_gaps = select_top_five(all_gaps)

    return Result(
        freelancer_id=freelancer_id,
        readiness=readiness,
        capped=all_self_declared,
        dimensions=dimensions,
        blocking=blocking or [],
        gaps=top_gaps,
        generated=GeneratedContent(),
    )
