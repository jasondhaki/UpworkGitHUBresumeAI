"""Synthetic-data check for skill_audit.py -- no Gemini/Ollama calls needed,
this is pure text/logic. Exercises exactly the three scenarios from the
feature request: a skill proven on GitHub but missing from Upwork, a skill
claimed everywhere but unproven on GitHub, and a required term missing
entirely.
"""

from datetime import date

from schemas.benchmark import Benchmark, RateBand, RequiredTerm
from schemas.claim import Claim, EvidenceTier, SourceSpan, SourceType
from app.scoring.skill_audit import STATUS_COVERED, STATUS_MISSING, STATUS_UNADVERTISED, STATUS_UNPROVEN, audit_skills


def make_claim(source_type, text, skill_ids, tier=EvidenceTier.T2):
    return Claim(
        claim_id=f"test_{hash(text)}",
        freelancer_id="fl_test",
        text=text,
        skill_ids=skill_ids,
        source_type=source_type,
        source_span=SourceSpan(document_id="test", start_index=0, end_index=len(text), extracted_text=text),
        tier=tier,
        observed_date=date.today(),
        publishable=True,
    )


BENCHMARK = Benchmark(
    niche="test-niche",
    required_terms=[
        RequiredTerm(term="python", synonyms=[]),
        RequiredTerm(term="ai automation", synonyms=["ai agent development"]),
    ],
    title_formula="{role} | {skills}",
    overview_words_min=50,
    overview_words_max=150,
    portfolio_min=2,
    rate_band=RateBand(min_hourly=20, max_hourly=100),
    dimension_targets={
        "positioning": 80, "evidence_quality": 80, "keyword_coverage": 80, "portfolio_quality": 80,
        "completeness": 80, "conversion": 80, "pricing_strategy": 80,
    },
    sample_size=0,
    built_date=date.today(),
)

claims = [
    # NextJS: claimed on CV, demonstrated on GitHub, NOT mentioned on Upwork.
    make_claim(SourceType.CV, "Tech: Next.js, TypeScript, Tailwind CSS", ["web_development_next_js"], EvidenceTier.T8),
    make_claim(SourceType.GITHUB, "Repository 'hopes-craft': primary language TypeScript.", ["typescript", "next", "react"]),
    make_claim(SourceType.UPWORK_PASTE, "I build automation workflows with n8n.", ["workflow_automation"], EvidenceTier.T8),
    # AI Automation: claimed on CV and Upwork, no GitHub evidence at all.
    make_claim(SourceType.CV, "Built an AI automation pipeline for a hackathon.", ["ai_model_automation"], EvidenceTier.T6),
    make_claim(SourceType.UPWORK_PASTE, "I specialize in AI automation for SMBs.", ["ai_agent_development"], EvidenceTier.T8),
    # Python: fully covered everywhere.
    make_claim(SourceType.CV, "Skills: Python, PyTorch", ["programming_languages_python"], EvidenceTier.T8),
    make_claim(SourceType.GITHUB, "Repository 'ml-tool': primary language Python.", ["python"]),
    make_claim(SourceType.UPWORK_PASTE, "I write production Python services.", ["python"], EvidenceTier.T8),
]

results = audit_skills(claims, BENCHMARK)

print(f"{len(results)} skill rows:\n")
for r in results:
    print(f"  [{r.status:26}] required={r.required!s:5} cv={r.on_cv!s:5} github={r.on_github!s:5} upwork={r.on_upwork!s:5}  {r.name}")

by_name = {r.name.lower(): r for r in results}

assert "python" in by_name and by_name["python"].status == STATUS_COVERED, "python should be fully covered"
assert by_name["ai automation"].status == STATUS_MISSING or by_name["ai automation"].status == STATUS_UNPROVEN, (
    "ai automation is claimed (CV+Upwork) but has zero GitHub evidence -- expected claimed_unproven"
)
assert by_name["ai automation"].status == STATUS_UNPROVEN, f"expected claimed_unproven, got {by_name['ai automation'].status}"

nextjs_rows = [r for r in results if "next" in r.name.lower()]
assert nextjs_rows, "expected a claimed-skill row for next.js/next"
nextjs = nextjs_rows[0]
assert nextjs.on_github and nextjs.on_cv and not nextjs.on_upwork, (
    f"next.js should be on_github=True, on_cv=True, on_upwork=False, got {nextjs}"
)
assert nextjs.status == STATUS_UNADVERTISED, f"expected demonstrated_not_advertised, got {nextjs.status}"

print("\nAll skill_audit checks passed.")
