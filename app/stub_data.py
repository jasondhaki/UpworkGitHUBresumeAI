"""Fake claims + benchmark, used only until real ingestion (Phase B) replaces them.
Deliberately the exact shapes real data will arrive in, so swapping this out later
is a data-source change, not a schema change.
"""

from datetime import date

from benchmarks.ai_ml_engineering_freelance import BENCHMARK as STUB_BENCHMARK
from schemas.claim import Claim, EvidenceTier, SourceType

STUB_MANUAL_SCORES = {
    "positioning": 55.0,
    "portfolio_quality": 60.0,
    "completeness": 70.0,
    "conversion": 40.0,
    "pricing_strategy": 50.0,
}


def stub_github_claim(github_username: str) -> list[Claim]:
    """GitHub API pull isn't built yet — Phase B. CV and Upwork-paste are real now
    (see app.ingestion.cv_parser / app.ingestion.upwork_parser)."""
    if not github_username.strip():
        return []
    return [
        Claim(
            claim_id="stub_github_1",
            freelancer_id="fl_stub",
            text=f"GitHub profile: {github_username.strip()} (stub — not yet pulled via API)",
            skill_ids=["skill_stub_github"],
            source_type=SourceType.GITHUB,
            tier=EvidenceTier.T2,
            observed_date=date(2026, 9, 1),
            publishable=True,
        )
    ]
