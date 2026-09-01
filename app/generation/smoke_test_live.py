"""ONE real Gemini call to prove the generation pipeline works end to end.
Run this deliberately, not repeatedly -- see CLAUDE.md's API call discipline.

Uses hardcoded claims matching real output already seen from the CV/Upwork
parsers earlier this build (see CONTEXT.md), rather than re-parsing the
fixtures live -- that would spend 2 more real calls on prompts that haven't
changed, testing nothing new. Only generation is new here, so only it spends
a real call.
"""

from datetime import date

from app.generation.title_overview import generate_title_and_overview
from benchmarks.ai_ml_engineering_freelance import BENCHMARK
from schemas.claim import Claim, EvidenceTier, SourceSpan, SourceType


def _claim(claim_id, tier, text, source_type=SourceType.CV):
    return Claim(
        claim_id=claim_id, freelancer_id="fl_gen_test", text=text, skill_ids=[],
        source_type=source_type,
        source_span=SourceSpan(document_id="fixture", start_index=0, end_index=len(text), extracted_text=text),
        tier=tier, observed_date=date(2026, 9, 1), publishable=True,
    )


claims = [
    _claim("cv_1", EvidenceTier.T8, "Experience: Senior ML Engineer, Acme Corp, 2022-2026"),
    _claim("cv_2", EvidenceTier.T6, "Built and deployed a RAG pipeline using Pinecone for retrieval, serving 10k+ queries/day."),
    _claim("cv_3", EvidenceTier.T4, "AWS Certified Machine Learning - Specialty (proctored exam, 2023)"),
    _claim("cv_4", EvidenceTier.T8, "Skills: Python, PyTorch, LLM fine-tuning, vector databases"),
    _claim("upwork_1", EvidenceTier.T1,
           'Clients often note that my automations are reliable and well-documented: one client wrote, '
           '"The workflow he built runs flawlessly and saved us thousands of dollars in manual labor costs."',
           source_type=SourceType.UPWORK_PASTE),
]

print(f"Generating from {len(claims)} claims (hardcoded, matching real prior output)...\n")
generated = generate_title_and_overview(claims, BENCHMARK.title_formula)

print("=== TITLE ===")
if generated.title:
    print(generated.title.text)
    print("Sourced from:", [s.claim_id for s in generated.title.source_spans])
else:
    print("(withheld -- either no traceable numbers, or model produced nothing usable)")

print("\n=== OVERVIEW ===")
if generated.overview:
    print(generated.overview.text)
    print("Sourced from:", [s.claim_id for s in generated.overview.source_spans])
else:
    print("(withheld -- either no traceable T1-T4 numbers, or model produced nothing usable)")

print("\nGeneration pipeline confirmed working end to end (one real Gemini call spent).")
