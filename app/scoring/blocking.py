"""Blocking-item detection (Section 3, rule 1): "Unproven claims, ToS risks,
missing identity verification are liabilities, not optimization opportunities
— they go in a separate fix-before-publishing list regardless of their
return on effort." Distinct from the ranked gap list — these aren't scored
opportunities, they're things to fix before a profile should go live at all.

Two checks implemented here, both deterministic and well-grounded in data
this system actually has. A third category from the spec — ToS risk — is
NOT implemented: there's no well-grounded, non-speculative way to detect
"ToS risk" from a claim set with what this build currently has (no client
NDAs, no platform terms, nothing to check against). Building a fake detector
just to populate the category would produce false confidence, which is
exactly what this whole system exists to prevent — so it's left out
honestly rather than faked.
"""

from schemas.benchmark import Benchmark
from schemas.claim import Claim, EvidenceTier
from schemas.result import BlockingItem

# Always true for Phase 1: "Accounts and login (hardcode one user)" is explicit
# out-of-scope (PROJECT_PLAN.md scope fence), so there is no identity
# verification mechanism at all yet, for any profile, ever. Flagging this
# honestly matches the plan's own example blocking item.
IDENTITY_VERIFICATION_ITEM = BlockingItem(
    description="No identity verification on file.",
    reason="missing identity verification",
)


def detect_unproven_core_claims(claims: list[Claim], benchmark: Benchmark) -> list[BlockingItem]:
    """For each of the niche's required skills that the profile claims to have,
    find the strongest evidence backing it. If the strongest evidence for a
    skill central to this niche is T8 (self-declared, no corroboration at
    all), that's a liability worth fixing before publishing — not just a
    scoring gap, since it's exactly the kind of unverifiable claim the whole
    system exists to catch (PROJECT_PLAN.md line 17).
    """
    items: list[BlockingItem] = []
    for rt in benchmark.required_terms:
        candidates = [rt.term.lower(), *[s.lower() for s in rt.synonyms]]
        matching = [c for c in claims if any(cand in c.text.lower() for cand in candidates)]
        if not matching:
            continue
        strongest = max(matching, key=lambda c: c.weight)
        if strongest.tier == EvidenceTier.T8:
            items.append(
                BlockingItem(
                    description=f'"{rt.term}" is claimed but the strongest evidence for it is '
                    "self-declared, with no corroboration at all.",
                    reason="unproven claim",
                )
            )
    return items


def detect_blocking_items(claims: list[Claim], benchmark: Benchmark) -> list[BlockingItem]:
    return [IDENTITY_VERIFICATION_ITEM, *detect_unproven_core_claims(claims, benchmark)]
