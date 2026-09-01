"""Real formulas for all seven scoring dimensions.

evidence_quality, keyword_coverage, completeness, and portfolio_quality are
fully deterministic — no judgment call involved, so no reason to spend a
Gemini call on them. positioning and conversion are inherently semantic per
Section 2's own wording ("stated specifically enough to be found and
believed", "addresses the buyer's problem") — implemented here as documented
rules-based PROXIES, not real semantic judgment, to avoid spending a Gemini
call per profile on something a cheap heuristic can approximate for a demo.
Each proxy's docstring says plainly what it actually checks vs. what the
dimension is supposed to measure — don't mistake the proxy for the real thing.
pricing_strategy is deterministic but needs one new input nothing collected
before: a stated hourly rate.
"""

import re

from schemas.benchmark import Benchmark
from schemas.claim import Claim, EvidenceTier
from schemas.result import GeneratedContent

SELF_DECLARED_CAP = 30.0  # Section 2: evidence dimension capped at 3/10 when every claim is self-declared
PROOF_ELIGIBLE_TIERS = {EvidenceTier.T1, EvidenceTier.T2, EvidenceTier.T3, EvidenceTier.T4}
NUMBER_PATTERN = re.compile(r"\d")


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


def compute_completeness(
    claims: list[Claim], generated: GeneratedContent | None, stated_rate: float | None
) -> float:
    """'Checklist of essential profile elements' (Section 2) — fully deterministic:
    presence/absence of the pieces the rest of this system actually produces or
    consumes. Equal-weighted; each item is either there or it isn't."""
    checks = [
        any(c.source_type.value == "cv" for c in claims),
        any(c.source_type.value == "github" for c in claims),
        any(c.source_type.value == "upwork_paste" for c in claims),
        any(c.tier in PROOF_ELIGIBLE_TIERS for c in claims),  # at least one T1-T4 (not purely self-declared)
        generated is not None and generated.title is not None,
        generated is not None and generated.overview is not None,
        stated_rate is not None,
        len({sid for c in claims for sid in c.skill_ids}) >= 5,  # breadth of skills mentioned
    ]
    return (sum(checks) / len(checks)) * 100


def compute_portfolio_quality(claims: list[Claim], benchmark: Benchmark) -> float:
    """'Item count, quantified results, working links' (Section 2) — three named
    sub-criteria, each scored and combined. "Portfolio items" = claims with real
    (not purely self-declared) evidence behind them, tiers T1-T4."""
    portfolio_items = [c for c in claims if c.tier in PROOF_ELIGIBLE_TIERS]
    if not portfolio_items:
        return 0.0

    count_score = min(len(portfolio_items) / max(benchmark.portfolio_min, 1), 1.0) * 50

    quantified = sum(1 for c in portfolio_items if NUMBER_PATTERN.search(c.text))
    quantified_score = (quantified / len(portfolio_items)) * 30

    working_links = sum(
        1 for c in portfolio_items if c.source_span and c.source_span.document_id.startswith("http")
    )
    link_score = (working_links / len(portfolio_items)) * 20

    return count_score + quantified_score + link_score


def compute_pricing_strategy(
    stated_rate: float | None, benchmark: Benchmark, evidence_quality_score: float
) -> float:
    """'Whether the stated rate is defensible given the evidence tier' (Section 2).
    Deterministic: a rate near the top of the band needs evidence_quality to
    roughly match; a modest rate is defensible regardless of evidence strength.
    No rate stated at all scores low — there's nothing to judge as defensible.
    """
    if stated_rate is None:
        return 0.0

    band = benchmark.rate_band
    span = max(band.max_hourly - band.min_hourly, 1.0)
    rate_fraction = max(0.0, min(1.0, (stated_rate - band.min_hourly) / span))
    evidence_fraction = evidence_quality_score / 100.0

    if rate_fraction <= evidence_fraction:
        return 100.0
    gap = rate_fraction - evidence_fraction
    return max(0.0, 100.0 - gap * 100.0)


def compute_positioning(claims: list[Claim], generated: GeneratedContent | None, benchmark: Benchmark) -> float:
    """PROXY for Section 2's 'role, vertical, and outcome stated specifically
    enough to be found and believed' — that's a semantic judgment call this
    function does NOT make. What it actually checks: whether generation
    produced grounded title/overview text at all (a claim set too thin to
    generate from is also too thin to position well), and whether that text
    touches enough of the niche's specific vocabulary and includes a concrete
    number (a structural proxy for "specific", not a specificity judgment).
    A real implementation would need an LLM or human rating "found and
    believed" — this doesn't attempt that.
    """
    if not claims or generated is None:
        return 0.0

    score = 0.0
    if generated.title is not None:
        score += 40
        if NUMBER_PATTERN.search(generated.title.text):
            score += 20
    if generated.overview is not None:
        score += 20

    text = " ".join(f.text.lower() for f in (generated.title, generated.overview) if f)
    terms_hit = sum(
        1
        for rt in benchmark.required_terms
        if rt.term.lower() in text or any(s.lower() in text for s in rt.synonyms)
    )
    if terms_hit >= 2:
        score += 20

    return min(score, 100.0)


def compute_conversion(generated: GeneratedContent | None) -> float:
    """PROXY for Section 2's 'whether the opening addresses the buyer's problem
    rather than describing the seller' — a real implementation needs semantic
    judgment of the opening line's framing. This checks only surface markers
    in the first ~20 words: self-referential openers ("I", "I'm", "My") count
    against it, buyer-facing/problem language ("you", "your", "struggl-",
    "tired of", "losing", "wasting") counts for it. Cheap, gameable, and not a
    substitute for actually reading the sentence — documented as such.
    """
    if generated is None or generated.overview is None:
        return 0.0

    words = generated.overview.text.split()[:20]
    opening = " ".join(words).lower()

    self_markers = sum(opening.count(m) for m in (" i ", "i'm ", "i am ", " my "))
    if opening.startswith(("i ", "i'm ", "i am ", "my ")):
        self_markers += 1
    buyer_markers = sum(
        opening.count(m) for m in ("you", "your", "struggl", "tired of", "losing", "wasting", "problem")
    )

    score = 50 + buyer_markers * 15 - self_markers * 15
    return max(0.0, min(100.0, score))
