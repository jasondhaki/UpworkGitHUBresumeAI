"""What's still not real, for the five dimensions without a formula yet
(see app/scoring/engine.py's docstring) and the benchmark re-export.

CV, Upwork-paste, and GitHub ingestion are all real now (app/ingestion/).
Only the five scoring dimensions without a Section-2 formula remain fake.
"""

from benchmarks.ai_ml_engineering_freelance import BENCHMARK as STUB_BENCHMARK

STUB_MANUAL_SCORES = {
    "positioning": 55.0,
    "portfolio_quality": 60.0,
    "completeness": 70.0,
    "conversion": 40.0,
    "pricing_strategy": 50.0,
}
