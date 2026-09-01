"""Tests the grounding validator directly, no Gemini call -- per CLAUDE.md's
API call discipline, this is exactly the kind of thing to verify with fakes
before ever spending a real call on it. Three cases: a clean draft that should
pass, a draft with a fabricated number that should be rejected, and an
overview draft that cites a real number but only from a non-proof-eligible
(T8) claim, which should also be rejected since overview numbers must trace
to T1-T4 material specifically.
"""

from datetime import date

from schemas.claim import Claim, EvidenceTier, SourceSpan, SourceType

from app.generation.title_overview import PROOF_ELIGIBLE_TIERS, _validate_and_build


def make_claim(claim_id: str, tier: EvidenceTier, text: str) -> Claim:
    return Claim(
        claim_id=claim_id,
        freelancer_id="fl_test",
        text=text,
        skill_ids=[],
        source_type=SourceType.CV,
        source_span=SourceSpan(document_id="doc", start_index=0, end_index=len(text), extracted_text=text),
        tier=tier,
        observed_date=date(2026, 9, 1),
        publishable=True,
    )


claims = [
    make_claim("c1", EvidenceTier.T2, "Built a RAG pipeline serving 10,000 queries per day."),
    make_claim("c2", EvidenceTier.T8, "I saved a client 95% of their manual work."),  # self-declared, not proof-eligible
]
claims_by_id = {c.claim_id: c for c in claims}
proof_eligible = [c for c in claims if c.tier in PROOF_ELIGIBLE_TIERS]

print("=== Case 1: clean draft, number matches a real T2 claim -> should PASS ===")
field = _validate_and_build(
    "AI Engineer who built a RAG pipeline handling 10,000 queries per day.",
    ["c1"], claims_by_id, allowed_claims=claims,
)
print("result:", field)
assert field is not None, "a real, traceable number should be accepted"
assert field.source_spans[0].claim_id == "c1"

print("\n=== Case 2: fabricated number (99%) not in any claim -> should be REJECTED ===")
field = _validate_and_build(
    "AI Engineer who improved efficiency by 99%.",
    ["c1"], claims_by_id, allowed_claims=claims,
)
print("result:", field)
assert field is None, "a fabricated number must be rejected, not published"

print("\n=== Case 3: overview cites a real number, but only from a T8 (non-proof-eligible) claim -> should be REJECTED ===")
field = _validate_and_build(
    "I saved a client 95% of their manual work.",
    ["c2"], claims_by_id, allowed_claims=proof_eligible,  # overview only gets T1-T4 in its allowed pool
)
print("result:", field)
assert field is None, "overview numbers must trace to T1-T4 claims specifically, even if the number is real elsewhere"

print("\nAll grounding-validator checks passed. No Gemini calls made.")
