"""Benchmark for the "ai-engineering-freelance" niche — RESEARCH-INFORMED, still PROVISIONAL.

=====================================================================
 STILL NOT THE FINAL BENCHMARK, but a real step up from the first pass.
 Upgraded 2026-09-02 using public secondary research (published rate
 reports, job-market skill-demand data, freelance-profile-writing best
 practice guides) — see BENCHMARK.md for the full methodology and every
 source cited. This is NOT built from reading actual top Upwork profiles;
 that step (PROJECT_PLAN.md Section 5's 30-profile hand-read) still hasn't
 happened, and deliberately can't be done by scraping Upwork itself —
 the plan explicitly rules that out (line 104), and Upwork's own site
 blocks bot access to its own published pages, which only confirms the
 boundary is real. `provisional=True` and `sample_size=0` stay in place
 honestly: this is a materially better-informed guess, not validated data.
=====================================================================

HOW TO UPGRADE THIS FILE once the real 30-profile read happens:
  1. Replace REQUIRED_TERMS with terms actually observed across the read
     profiles (add/remove/adjust synonyms based on what real listings use) —
     the current list is demand-side (what the job market wants), not
     supply-side (what winning profiles actually say); those can differ.
  2. Replace RATE_BAND with the actual observed rate spread from real profiles
     — the current band is market-wide survey data, not Upwork-specific.
  3. Replace DIMENSION_TARGETS with values that reflect what the top profiles
     actually hit on each dimension — these remain the least-informed part
     of this file; research couldn't meaningfully validate them without
     reading real profiles (see BENCHMARK.md's Confidence section).
  4. Set sample_size to the real count and provisional=False.
  5. Fill in source_notes with when/how the read was done.
  6. Update built_date.
title_formula and the overview structure are now backed by general
profile-writing research (see BENCHMARK.md) rather than pure guesswork,
so they're a lighter lift to verify — the shape is probably right, the
exact wording is what real-profile reading would refine.
"""

from datetime import date

from schemas.benchmark import Benchmark, RateBand, RequiredTerm

# Demand-side vocabulary — reflects what job postings and hiring guides say the
# market wants in 2026 (agentic AI / multi-agent orchestration and LangChain
# grew sharply since 2024; see BENCHMARK.md). Still not confirmed as what
# actually appears in winning Upwork profile text specifically.
REQUIRED_TERMS = [
    RequiredTerm(term="LLM", synonyms=["large language model", "large language models"]),
    RequiredTerm(term="RAG", synonyms=["retrieval augmented generation", "retrieval-augmented generation"]),
    RequiredTerm(
        term="vector database",
        synonyms=["pinecone", "weaviate", "qdrant", "chroma", "milvus", "pgvector"],
    ),
    RequiredTerm(
        term="agent framework",
        synonyms=["langchain", "langgraph", "llamaindex", "autogen", "crewai"],
    ),
    RequiredTerm(
        term="agentic AI",
        synonyms=["multi-agent orchestration", "ai agents", "agentic workflows", "multi-agent systems"],
    ),
    RequiredTerm(term="prompt engineering", synonyms=["prompt design"]),
    RequiredTerm(term="LLM fine-tuning", synonyms=["fine-tune", "fine-tuning", "lora", "qlora"]),
    RequiredTerm(term="generative AI", synonyms=["genai", "gen ai"]),
    RequiredTerm(term="LLM API integration", synonyms=["openai api", "anthropic api", "gemini api"]),
    RequiredTerm(term="Python", synonyms=[]),
    RequiredTerm(term="deep learning framework", synonyms=["pytorch", "tensorflow"]),
    RequiredTerm(term="MLOps", synonyms=["model deployment", "model serving", "ml pipelines"]),
    RequiredTerm(term="containerization", synonyms=["docker", "kubernetes"]),
    RequiredTerm(term="cloud platform", synonyms=["aws", "gcp", "azure"]),
    RequiredTerm(term="NLP", synonyms=["natural language processing"]),
    RequiredTerm(term="embeddings", synonyms=["semantic search"]),
    RequiredTerm(term="LLM evaluation", synonyms=["llm evals", "model evaluation"]),
]

# Market-wide survey data (multiple 2026 freelance-rate reports), not
# Upwork-specific and not filtered to "top tier only" -- spans junior through
# senior so it stays a meaningful reference band for the pricing_strategy
# dimension regardless of where a given profile's evidence tier lands.
# Full spread found in research: $40-400/hr depending on seniority, geography,
# and specialization -- see BENCHMARK.md. This band is the broad defensible
# middle, not the extremes.
RATE_BAND = RateBand(currency="USD", min_hourly=60, max_hourly=250)

# Least research-backed part of this file -- these are still reasoned
# estimates of what top profiles achieve per dimension (0-100 scale), not
# something public market research can validate directly. See BENCHMARK.md's
# Confidence Level section.
DIMENSION_TARGETS = {
    "positioning": 85,
    "evidence_quality": 80,
    "keyword_coverage": 90,
    "portfolio_quality": 85,
    "completeness": 95,
    "conversion": 75,
    "pricing_strategy": 80,
}

BENCHMARK = Benchmark(
    niche="ai-engineering-freelance",
    required_terms=REQUIRED_TERMS,
    # "Effective titles combine primary specialty, niche differentiator, and
    # value driver" -- matches the structure already in place; research
    # confirmed the shape rather than changing it. See BENCHMARK.md.
    title_formula="{role} | {specialization} | {measurable outcome}",
    overview_words_min=150,
    overview_words_max=300,
    portfolio_min=3,  # "the right five, presented well" per research; 3 as a floor, not a ceiling
    rate_band=RATE_BAND,
    dimension_targets=DIMENSION_TARGETS,
    sample_size=0,  # no real profiles read yet — see module docstring
    built_date=date(2026, 9, 2),
    provisional=True,
    source_notes=(
        "Upgraded from a pure-guess placeholder to research-informed on 2026-09-02, using public "
        "secondary sources (rate reports, job-market skill-demand data, profile-writing best-practice "
        "guides) -- NOT from reading real Upwork profiles, and deliberately not from scraping Upwork "
        "(PROJECT_PLAN.md line 104; Upwork's own site also blocks bot access, confirming the boundary). "
        "Full methodology and every source cited in BENCHMARK.md. Still needs the real 30-profile "
        "hand-read to become non-provisional."
    ),
)
