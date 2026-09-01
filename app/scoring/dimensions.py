"""Real formulas for the two dimensions Section 2 fully specifies.

The other five (positioning, portfolio_quality, completeness, conversion,
pricing_strategy) need semantic judgment the plan doesn't reduce to a formula —
those stay as caller-supplied inputs until Phase B/C ingestion and generation
exist to feed them for real.
"""

from schemas.benchmark import Benchmark
from schemas.claim import Claim, EvidenceTier

SELF_DECLARED_CAP = 30.0  # Section 2: evidence dimension capped at 3/10 when every claim is self-declared


def compute_evidence_quality(claims: list[Claim]) -> tuple[float, bool]:
    """'A skill takes its strongest evidence, never the sum of weak evidence' (Section 2).

    Returns (score_0_100, all_self_declared). all_self_declared drives both the
    per-dimension cap here and the separate overall-readiness cap in engine.py.
    """
    if not claims:
        return 0.0, True

    strongest_per_skill: dict[str, Claim] = {}
    for claim in claims:
        for skill_id in claim.skill_ids:
            current = strongest_per_skill.get(skill_id)
            if current is None or claim.weight > current.weight:
                strongest_per_skill[skill_id] = claim

    if not strongest_per_skill:
        return 0.0, True

    avg_weight = sum(c.weight for c in strongest_per_skill.values()) / len(strongest_per_skill)
    score = avg_weight * 100

    all_self_declared = all(c.tier == EvidenceTier.T8 for c in strongest_per_skill.values())
    if all_self_declared:
        score = min(score, SELF_DECLARED_CAP)

    return score, all_self_declared


def compute_keyword_coverage(claims: list[Claim], benchmark: Benchmark) -> float:
    """Presence, not frequency (Section 2): a term counts once it's found anywhere,
    repeating it changes nothing. Matched via the benchmark's synonym table first —
    NOT embeddings, per the tested finding that general embeddings don't reliably
    encode e.g. "Pinecone is a vector database" (see PROJECT_PLAN.md Section 2 note).
    """
    if not benchmark.required_terms:
        return 100.0

    combined_text = " ".join(c.text.lower() for c in claims)

    covered = 0
    for rt in benchmark.required_terms:
        candidates = [rt.term.lower(), *[s.lower() for s in rt.synonyms]]
        if any(candidate in combined_text for candidate in candidates):
            covered += 1

    return (covered / len(benchmark.required_terms)) * 100
