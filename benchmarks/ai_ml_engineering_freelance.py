"""Benchmark for the "ai-engineering-freelance" niche — PROVISIONAL.

=====================================================================
 THIS IS NOT THE REAL BENCHMARK. It's a placeholder so Phase A/B could
 keep moving instead of blocking entirely on the 30-profile read-through
 (PROJECT_PLAN.md Section 5). Every number below is a best-guess estimate
 from general knowledge of the AI/ML freelance market, NOT from reading
 actual top-performing Upwork profiles. `provisional=True` and
 `sample_size=0` on the Benchmark object reflect that honestly — nothing
 downstream should treat this as validated data.
=====================================================================

HOW TO UPGRADE THIS FILE once the real 30-profile read happens:
  1. Replace REQUIRED_TERMS with terms actually observed across the read
     profiles (add/remove/adjust synonyms based on what real listings use).
  2. Replace RATE_BAND with the actual observed rate spread.
  3. Replace DIMENSION_TARGETS with values that reflect what the top
     profiles actually hit on each dimension — these are currently just
     "high but not perfect" guesses, not measurements.
  4. Set sample_size to the real count and provisional=False.
  5. Fill in source_notes with when/how the read was done.
  6. Update built_date.
Everything else (title_formula shape, overview length band, portfolio_min)
is a lighter lift to verify and less likely to need major changes.
"""

from datetime import date

from schemas.benchmark import Benchmark, RateBand, RequiredTerm

# Core technical vocabulary for AI/ML engineering freelance work as of general
# knowledge — likely incomplete, and definitely not weighted by actual
# frequency across real top profiles yet. Treat gaps here as expected.
REQUIRED_TERMS = [
    RequiredTerm(term="RAG", synonyms=["retrieval augmented generation", "retrieval-augmented generation"]),
    RequiredTerm(
        term="vector database",
        synonyms=["pinecone", "weaviate", "qdrant", "chroma", "milvus", "pgvector"],
    ),
    RequiredTerm(term="LLM fine-tuning", synonyms=["fine-tune", "fine-tuning", "lora", "qlora"]),
    RequiredTerm(term="prompt engineering", synonyms=["prompt design"]),
    RequiredTerm(
        term="agent framework",
        synonyms=["langchain", "llamaindex", "autogen", "crewai", "agentic workflows", "ai agents"],
    ),
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

# Genuinely uncertain — freelance AI engineering rates vary enormously by
# seniority and specialization. This is a wide guess band, not a researched one.
RATE_BAND = RateBand(currency="USD", min_hourly=50, max_hourly=150)

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
    title_formula="{role} | {specialization} | {measurable outcome}",
    overview_words_min=150,
    overview_words_max=300,
    portfolio_min=3,
    rate_band=RATE_BAND,
    dimension_targets=DIMENSION_TARGETS,
    sample_size=0,  # no real profiles read yet — see module docstring
    built_date=date(2026, 9, 1),
    provisional=True,
    source_notes=(
        "Built from general knowledge of the AI/ML freelance market, not from reading real "
        "Upwork profiles. Needs the 30-profile hand-read (PROJECT_PLAN.md Section 5) to become "
        "real data. See this file's module docstring for exactly what to update."
    ),
)
