"""Proves the real CV path: a real PDF produces real Claim records, then feeds
them straight into the (already-proven) scoring engine. This is the first
place in the build where a genuine document goes all the way through.
"""

from app.ingestion.cv_parser import parse_cv_to_claims
from app.scoring.engine import score_profile
from app.stub_data import STUB_BENCHMARK, STUB_MANUAL_SCORES

PDF_PATH = "scripts/fixtures_sample_cv.pdf"

claims = parse_cv_to_claims(PDF_PATH, freelancer_id="fl_real_cv_test")

print(f"Extracted {len(claims)} claims from {PDF_PATH}:\n")
for c in claims:
    print(f"  tier={c.tier.value:3} weight={c.weight:.2f} skills={c.skill_ids}")
    print(f"    text: {c.text!r}")
    print(f"    span: [{c.source_span.start_index}:{c.source_span.end_index}] matches text: "
          f"{c.source_span.extracted_text == c.text}")

assert len(claims) > 0, "expected at least one claim from a CV with real content"
assert all(c.source_span is not None for c in claims), "every CV claim must carry a source span"
assert all(c.source_span.extracted_text == c.text for c in claims), "span text must match claim text exactly"

result = score_profile(
    freelancer_id="fl_real_cv_test",
    claims=claims,
    benchmark=STUB_BENCHMARK,
    manual_dimension_scores=STUB_MANUAL_SCORES,
)
print(f"\nreadiness: {result.readiness} | capped: {result.capped}")
print(f"evidence_quality: {result.dimensions['evidence_quality'].current:.1f}")
print(f"keyword_coverage: {result.dimensions['keyword_coverage'].current:.1f}")

print("\nReal CV -> real claims -> real score. Phase A ingestion path confirmed working.")
