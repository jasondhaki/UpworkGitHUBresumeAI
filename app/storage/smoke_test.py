"""Storage round-trip with fake data. No Gemini calls -- pure persistence logic."""

from datetime import date

from schemas.claim import Claim, EvidenceTier, SourceSpan, SourceType
from schemas.result import DimensionScore, Result

from app.storage.files import save_uploaded_file
from app.storage.repository import get_analysis_run, list_analysis_runs, save_analysis_run

# --- files.py ---
path = save_uploaded_file(b"%PDF-1.4 fake content", "resume.pdf")
print(f"Saved file to: {path}")
assert path.exists(), "file should actually be written to disk"
assert path.read_bytes() == b"%PDF-1.4 fake content"

# --- repository.py round-trip ---
claim = Claim(
    claim_id="clm_1", freelancer_id="fl_storage_test", text="Built a RAG pipeline.",
    skill_ids=["rag"], source_type=SourceType.CV,
    source_span=SourceSpan(document_id=str(path), start_index=0, end_index=22, extracted_text="Built a RAG pipeline."),
    tier=EvidenceTier.T2, observed_date=date(2026, 9, 1), publishable=True,
)
dims = {name: DimensionScore(current=50, target=80, weight=w) for name, w in {
    "positioning": 0.22, "evidence_quality": 0.22, "keyword_coverage": 0.15,
    "portfolio_quality": 0.15, "completeness": 0.10, "conversion": 0.08, "pricing_strategy": 0.08,
}.items()}
result = Result(freelancer_id="fl_storage_test", readiness=45, capped=False, dimensions=dims)

run_id = save_analysis_run("fl_storage_test", [claim], result)
print(f"Saved run: {run_id}")

fetched = get_analysis_run(run_id)
assert fetched is not None, "should be able to fetch a run that was just saved"
fetched_result, fetched_claims = fetched
assert fetched_result.readiness == 45
assert len(fetched_claims) == 1
assert fetched_claims[0].text == "Built a RAG pipeline."
assert fetched_claims[0].tier == EvidenceTier.T2
assert fetched_claims[0].weight == 0.85, "computed field should survive the round trip"
print("Fetched run matches what was saved, including the computed 'weight' field.")

summaries = list_analysis_runs("fl_storage_test")
assert any(s["run_id"] == run_id for s in summaries), "the saved run should show up in the list"
print(f"list_analysis_runs found {len(summaries)} run(s) for this freelancer.")

assert get_analysis_run("nonexistent") is None, "a missing run_id should return None, not raise"

print("\nStorage round-trip confirmed working.")
