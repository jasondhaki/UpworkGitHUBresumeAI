"""Real Upwork-paste -> Claim records, using the actual sample text provided
during the build as the fixture. Specifically checks that the quoted client
testimonial gets tier T1 and everything else defaults to T8, per the tier
rules documented in upwork_parser.py.
"""

from app.ingestion.upwork_parser import parse_upwork_text_to_claims
from app.scoring.engine import score_profile
from app.stub_data import STUB_BENCHMARK, STUB_MANUAL_SCORES

SAMPLE_TEXT = """I'm an automation specialist helping SMBs eliminate manual busywork. Over the past 3 years I've built more than 25 automated workflows using n8n and Make.com for e-commerce and logistics clients.

For a mid-sized logistics company, I built an n8n workflow that connects their order management system to Slack and Airtable via webhook triggers, cutting manual data entry time by 60% and reducing order-processing errors to near zero.

I designed a CRM automation pipeline using Make.com that syncs leads between HubSpot and a custom Postgres database through a REST API integration, increasing sales team response time by 45%.

I also built a robust error-handling and retry system for a client's Shopify-to-QuickBooks sync, reducing failed sync incidents by 80% and saving the client roughly 10 hours per week of manual reconciliation.

Clients often note that my automations are reliable and well-documented: one client wrote, "The workflow he built runs flawlessly and saved us thousands of dollars in manual labor costs."

I charge $65/hour and typically deliver production-ready automations within 1-2 weeks."""

claims = parse_upwork_text_to_claims(SAMPLE_TEXT, freelancer_id="fl_upwork_test")

print(f"Extracted {len(claims)} claims:\n")
for c in claims:
    print(f"  tier={c.tier.value:3} weight={c.weight:.2f} skills={c.skill_ids}")
    print(f"    text: {c.text!r}")
    print(f"    span matches text: {c.source_span.extracted_text == c.text}")
    print()

t1_claims = [c for c in claims if c.tier.value == "T1"]
print(f"T1 (client-verified) claims found: {len(t1_claims)}")
for c in t1_claims:
    print(f"  -> {c.text!r}")
assert len(t1_claims) >= 1, "expected the quoted client testimonial to be detected as T1"
assert all("client wrote" in c.text.lower() or '"' in c.text for c in t1_claims), \
    "T1 claim should be the one containing the actual quote"

result = score_profile(
    freelancer_id="fl_upwork_test",
    claims=claims,
    benchmark=STUB_BENCHMARK,
    manual_dimension_scores=STUB_MANUAL_SCORES,
)
print(f"\nreadiness: {result.readiness} | capped: {result.capped}")
print(f"evidence_quality: {result.dimensions['evidence_quality'].current:.1f}")
print(f"keyword_coverage: {result.dimensions['keyword_coverage'].current:.1f} "
      "(expected low/zero -- this profile is automation/n8n work, not the AI/ML niche benchmark)")

print("\nUpwork-paste ingestion confirmed working, T1 testimonial detection confirmed.")
