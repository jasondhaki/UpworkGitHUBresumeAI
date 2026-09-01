"""Benchmark for the "ai-engineering-freelance" niche — REAL DATA, non-provisional.

=====================================================================
 Built from the actual 30-profile hand-read (PROJECT_PLAN.md Section 5),
 done 2026-09-02: 30 real Top Rated / Top Rated Plus Upwork profiles
 (~10 each across AI Engineer / Machine Learning Engineer / LLM Engineer
 searches), collected manually by the user — never scraped, matching the
 plan's own boundary. Raw profile data lives only in the gitignored
 research/30BestProfiles.md — per Section 3's own Anchor-track principle
 ("extracts structural patterns... then discards the source profiles —
 only aggregate patterns are kept"), only the derived aggregates below
 are committed. See BENCHMARK.md for the full methodology, every number's
 derivation, and what's still lower-confidence.

 `provisional` is now False: required_terms, rate_band, portfolio_min, and
 title_formula are all real, computed from the 30-profile sample, not
 estimates. `dimension_targets` is the one exception — see its comment
 below and BENCHMARK.md's Confidence Level section; that field still
 can't be derived directly from profile text.
=====================================================================
"""

from datetime import date

from schemas.benchmark import Benchmark, RateBand, RequiredTerm

# Frequency-ranked from the real 30-profile sample's skills tags (exact counts
# in BENCHMARK.md). Genuine corrections from the earlier job-posting-based
# guess: "Machine Learning" (24/30), "Artificial Intelligence" (22/30),
# "Deep Learning" (17/30), "Computer Vision" (9/30), and "Chatbot Development"
# / "AI Chatbot" (9+10/30) were all absent from the old list despite being
# extremely common self-tags; "n8n" (6/30) turned up as a real, notable
# pattern research never surfaced. Conversely "MLOps" (2/30), containerization
# (~1/30), and "LLM evaluation" (0/30 as an explicit tag) were carried over
# from job-market research but barely appear as real profile tags -- kept,
# since they're still legitimate underlying skills, but their real-world
# term-matching value is now known to be low.
REQUIRED_TERMS = [
    RequiredTerm(term="Python", synonyms=[]),  # 25/30
    RequiredTerm(term="Machine Learning", synonyms=["ML"]),  # 24/30
    RequiredTerm(term="Artificial Intelligence", synonyms=["AI"]),  # 22/30
    RequiredTerm(
        term="AI agent development",
        synonyms=["ai agents", "agentic ai", "multi-agent", "agentic workflows"],
    ),  # 19/30 -- more dominant as a literal self-tag than the earlier job-posting research suggested
    RequiredTerm(term="deep learning", synonyms=["deep neural network"]),  # 17/30
    RequiredTerm(term="RAG", synonyms=["retrieval augmented generation", "retrieval-augmented generation"]),  # 15/30
    RequiredTerm(term="agent framework", synonyms=["langchain", "langgraph", "llamaindex", "autogen", "crewai"]),  # 14/30
    RequiredTerm(term="LLM API integration", synonyms=["openai api", "anthropic api", "gemini api"]),  # 13/30
    RequiredTerm(term="NLP", synonyms=["natural language processing"]),  # 13/30
    RequiredTerm(term="prompt engineering", synonyms=["llm prompt engineering", "prompt design"]),  # 12/30
    RequiredTerm(term="LLM", synonyms=["large language model", "large language models"]),  # 10/30
    RequiredTerm(term="chatbot development", synonyms=["ai chatbot", "conversational ai"]),  # 9+10/30
    RequiredTerm(term="AI app development", synonyms=[]),  # 9/30
    RequiredTerm(term="generative AI", synonyms=["genai", "gen ai"]),  # 9/30
    RequiredTerm(term="computer vision", synonyms=["opencv", "yolo", "image processing"]),  # 9/30 -- not in the old list at all
    RequiredTerm(term="Claude", synonyms=["anthropic claude"]),  # 8/30
    RequiredTerm(
        term="vector database", synonyms=["pinecone", "weaviate", "qdrant", "chroma", "milvus", "pgvector"]
    ),  # 7/30
    RequiredTerm(term="deep learning framework", synonyms=["pytorch", "tensorflow"]),  # 8+7/30
    RequiredTerm(term="automation", synonyms=["n8n", "workflow automation", "zapier", "make.com"]),  # 6+6/30 -- new finding, not in earlier research at all
    RequiredTerm(term="fastapi", synonyms=[]),  # 5/30
    RequiredTerm(term="cloud platform", synonyms=["aws", "amazon web services", "gcp", "azure"]),  # ~5-6/30 combined
    RequiredTerm(term="LLM fine-tuning", synonyms=["fine-tune", "fine-tuning", "lora", "qlora"]),  # present but less tagged than expected
    RequiredTerm(term="MLOps", synonyms=["model deployment", "model serving", "ml pipelines"]),  # only 2/30 as an explicit tag -- kept, low real-tag confidence
    RequiredTerm(term="containerization", synonyms=["docker", "kubernetes"]),  # ~1/30 as an explicit tag -- kept, low real-tag confidence
]

# Real distribution from the 30-profile sample: min $15/hr, max $120/hr,
# median $35/hr, mean $42.27/hr. Notably lower than the earlier market-wide
# survey data ($118-195/hr average for "experienced" freelancers per generic
# rate reports) -- Upwork itself, even among Top Rated/Top Rated Plus
# profiles, runs meaningfully more price-competitive than broad market
# surveys suggested. Using the real observed min/max rather than a trimmed
# range: this is real Top-Rated data, not a guess that needs hedging.
RATE_BAND = RateBand(currency="USD", min_hourly=15, max_hourly=120)

# Still the least research-backed part of this file -- what "good" looks like
# on the system's own 0-100 dimension scales isn't something profile text
# directly encodes; the 30-profile sample gives strong signal on WHAT to
# measure (see REQUIRED_TERMS, RATE_BAND, portfolio_min, title_formula below)
# but not directly what score a top profile would get from THIS system's own
# formulas. Real values, not just a placeholder guess this time, but still
# the field most likely to need revision. See BENCHMARK.md's Confidence
# Level section.
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
    # Real finding, not the earlier guess: only 1/30 titles contained any digit
    # at all, and that one was a project count ("200+ AI Projects"), not a
    # client outcome. Measurable outcomes live in the OVERVIEW in real
    # profiles, not the title -- dropped "measurable outcome" from the title
    # formula itself to match what actually works.
    title_formula="{role/seniority} | {specialization or key technologies}",
    overview_words_min=150,
    overview_words_max=300,
    portfolio_min=3,  # real median across the sample is ~7-8 items, but portfolio_min stays a floor: one $85/hr profile had zero portfolio items, backed by work history instead
    rate_band=RATE_BAND,
    dimension_targets=DIMENSION_TARGETS,
    sample_size=30,
    built_date=date(2026, 9, 2),
    provisional=False,
    source_notes=(
        "Built from a real 30-profile hand-read of Top Rated / Top Rated Plus Upwork profiles "
        "(~10 each: AI Engineer / Machine Learning Engineer / LLM Engineer), collected manually by "
        "the user 2026-09-02 -- never scraped. required_terms, rate_band, portfolio_min, and "
        "title_formula are computed directly from this sample. dimension_targets remains a reasoned "
        "estimate, not directly derivable from profile text -- see BENCHMARK.md's Confidence Level "
        "section. Raw profile data is intentionally not in this repo (gitignored, research/); only "
        "these aggregate patterns are, per PROJECT_PLAN.md Section 3's own Anchor-track principle."
    ),
)
