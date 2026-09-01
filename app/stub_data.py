"""Re-exports the active benchmark for the app to import.

All seven scoring dimensions now have real formulas (app/scoring/engine.py) —
there's no longer any manual/placeholder dimension data. This module is a
thin re-export at this point; kept as a separate module in case a future
niche switch needs to swap which benchmark file gets imported here.
"""

from benchmarks.ai_ml_engineering_freelance import BENCHMARK as STUB_BENCHMARK
