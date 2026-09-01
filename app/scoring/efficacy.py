"""Versioned efficacy lookup (Section 2's gap-ranking formula).

efficacy = expected share of a dimension's gap that a typical fix actually closes.
Starter values only — "refined over time from outcome data" per the plan, meaning
once real profiles have gone through the system and been re-scored after acting on
gaps, these numbers should be replaced with observed values, not re-guessed.
Bump EFFICACY_VERSION whenever these change so a past score stays explainable.
"""

EFFICACY_VERSION = "v1-2026-09-01-starter"

EFFICACY: dict[str, float] = {
    "positioning": 0.6,
    "evidence_quality": 0.5,  # needs new proof, not just a rewrite — slower to fully close
    "keyword_coverage": 0.8,  # mostly a rewrite exercise once the required terms are known
    "portfolio_quality": 0.4,
    "completeness": 0.9,  # checklist items are close to fully closeable in one pass
    "conversion": 0.6,
    "pricing_strategy": 0.7,
}
DEFAULT_EFFICACY = 0.5

EFFORT_HOURS: dict[str, float] = {
    "positioning": 1.0,
    "evidence_quality": 6.0,
    "keyword_coverage": 1.0,
    "portfolio_quality": 4.0,
    "completeness": 0.5,
    "conversion": 1.5,
    "pricing_strategy": 0.5,
}
DEFAULT_EFFORT_HOURS = 1.0
