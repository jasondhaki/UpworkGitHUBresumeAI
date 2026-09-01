"""Ties dimensions.py + gap_ranking.py together into a Result.

score_profile() is the one function the rest of the app calls. All seven
dimensions now have real formulas (see dimensions.py — two exact per Section
2, two fully deterministic checklists, one deterministic given a stated rate,
and two documented rules-based proxies for the inherently semantic ones).
`generated` must be computed BEFORE calling this — positioning and
conversion read the generated title/overview, so generation runs first in
the actual request flow (app/main.py), not after scoring like it used to.
"""

from schemas.benchmark import DIMENSIONS, Benchmark
from schemas.claim import Claim
from schemas.result import BlockingItem, DimensionScore, GeneratedContent, Result

from .dimensions import (
    compute_completeness,
    compute_conversion,
    compute_evidence_quality,
    compute_keyword_coverage,
    compute_portfolio_quality,
    compute_positioning,
    compute_pricing_strategy,
)
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
    generated: GeneratedContent | None = None,
    stated_rate: float | None = None,
    blocking: list[BlockingItem] | None = None,
) -> Result:
    generated = generated or GeneratedContent()

    evidence_score, all_self_declared = compute_evidence_quality(claims)
    keyword_score = compute_keyword_coverage(claims, benchmark)

    raw_scores = {
        "positioning": compute_positioning(claims, generated, benchmark),
        "evidence_quality": evidence_score,
        "keyword_coverage": keyword_score,
        "portfolio_quality": compute_portfolio_quality(claims, benchmark),
        "completeness": compute_completeness(claims, generated, stated_rate),
        "conversion": compute_conversion(generated),
        "pricing_strategy": compute_pricing_strategy(stated_rate, benchmark, evidence_score),
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
        generated=generated,
    )
