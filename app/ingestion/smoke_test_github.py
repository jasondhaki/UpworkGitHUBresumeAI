"""Real GitHub API -> Claim records. No Gemini calls here (see github_parser.py
docstring for why) — safe to run freely, doesn't touch the Gemini rate limit.
"""

from app.ingestion.github_parser import parse_github_to_claims
from app.scoring.engine import score_profile
from app.stub_data import STUB_BENCHMARK, STUB_MANUAL_SCORES

claims = parse_github_to_claims("torvalds", freelancer_id="fl_github_test")

print(f"Extracted {len(claims)} claims:\n")
for c in claims:
    print(f"  tier={c.tier.value:3} weight={c.weight:.2f} skills={c.skill_ids}")
    print(f"    text: {c.text!r}")
    print(f"    source: {c.source_span.document_id}")
    print()

assert len(claims) > 0, "expected at least one non-fork repo claim"
assert all(c.tier.value == "T2" for c in claims), "all GitHub claims should be T2"
assert all(c.source_span.document_id.startswith("https://github.com/") for c in claims), \
    "source_span should point at a real, clickable repo URL"

result = score_profile(
    freelancer_id="fl_github_test",
    claims=claims,
    benchmark=STUB_BENCHMARK,
    manual_dimension_scores=STUB_MANUAL_SCORES,
)
print(f"readiness: {result.readiness} | capped: {result.capped}")
print(f"evidence_quality: {result.dimensions['evidence_quality'].current:.1f}")

print("\nGitHub ingestion confirmed working — zero Gemini calls made.")
